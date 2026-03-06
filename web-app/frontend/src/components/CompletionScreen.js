import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import './CompletionScreen.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_BASE_URL || 'http://localhost:8080';
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 2000;

function CompletionScreen({ participantId, prolificId }) {
  const [completionUrl, setCompletionUrl] = useState('');
  const [completionCode, setCompletionCode] = useState('');
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  const fetchCompletionUrl = useCallback(async () => {
    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/completion/prolific`, {
          params: { participant_id: participantId, prolific_id: prolificId }
        });
        setCompletionUrl(response.data.completion_url || '');
        setCompletionCode(response.data.completion_code || '');
        setLoading(false);
        return;
      } catch (error) {
        console.error(`Completion URL fetch attempt ${attempt}/${MAX_RETRIES} failed:`, error);
        if (attempt < MAX_RETRIES) {
          await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
        }
      }
    }
    setFailed(true);
    setLoading(false);
  }, [participantId, prolificId]);

  useEffect(() => {
    fetchCompletionUrl();
  }, [fetchCompletionUrl]);

  const handleRedirect = () => {
    if (completionUrl) {
      window.location.href = completionUrl;
    }
  };

  const renderFallback = () => {
    if (completionCode) {
      return (
        <p className="completion-url-info">
          Please return to Prolific and enter your completion code: <strong>{completionCode}</strong>
        </p>
      );
    }
    return (
      <p className="completion-url-info">
        Please return to Prolific and confirm your submission there.
      </p>
    );
  };

  return (
    <div className="completion-screen">
      <div className="completion-content">
        <h1>Thank You!</h1>
        <p>
          You have completed the study. Your responses have been recorded.
        </p>
        <p>
          We appreciate your participation in this research.
        </p>
        {loading ? (
          <p>Loading completion link...</p>
        ) : completionUrl ? (
          <button className="completion-button" onClick={handleRedirect}>
            Return to Prolific
          </button>
        ) : failed ? (
          renderFallback()
        ) : (
          renderFallback()
        )}
      </div>
    </div>
  );
}

export default CompletionScreen;
