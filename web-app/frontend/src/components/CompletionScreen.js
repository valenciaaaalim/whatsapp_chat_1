import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './CompletionScreen.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function CompletionScreen({ participantId }) {
  const [completionUrl, setCompletionUrl] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCompletionUrl();
  }, [participantId]);

  const fetchCompletionUrl = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/completion/prolific`, {
        params: { participant_id: participantId }
      });
      setCompletionUrl(response.data.completion_url);
    } catch (error) {
      console.error('Error fetching completion URL:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRedirect = () => {
    if (completionUrl) {
      window.location.href = completionUrl;
    }
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
        ) : (
          <p className="completion-url-info">
            If you were referred from Prolific, please use your completion code.
          </p>
        )}
      </div>
    </div>
  );
}

export default CompletionScreen;

