import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from 'react-router-dom';
import axios from 'axios';
import WelcomeScreen from './components/WelcomeScreen';
import ConversationScreen from './components/ConversationScreen';
import SurveyScreen from './components/SurveyScreen';
import CompletionScreen from './components/CompletionScreen';
import AlreadyCompletedScreen from './components/AlreadyCompletedScreen';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const PROLIFIC_STORAGE_KEY = 'whatsapp_prolific_id';

// Component to handle conversation route with index parameter
function ConversationRoute({ conversations, sessionIds, participantId, prolificId, variant, onComplete }) {
  const { index } = useParams();
  const conversationIndex = parseInt(index || '0', 10);
  
  if (conversations.length === 0) {
    return <div className="loading">Loading conversations...</div>;
  }
  
  if (conversationIndex >= conversations.length || conversationIndex < 0) {
    return <Navigate to="/completion" />;
  }
  
  return (
    <ConversationScreen
      conversation={conversations[conversationIndex]}
      sessionId={sessionIds[conversationIndex]}
      participantId={participantId}
      participantProlificId={prolificId}
      variant={variant}
      onComplete={onComplete}
      conversationIndex={conversationIndex}
    />
  );
}

function App() {
  const [participantId, setParticipantId] = useState(null);
  const [variant, setVariant] = useState(null);
  const [participantStatus, setParticipantStatus] = useState('new');
  const [completionUrl, setCompletionUrl] = useState('');
  const [prolificId, setProlificId] = useState('');
  const [currentConversationIndex, setCurrentConversationIndex] = useState(0);
  const [conversations, setConversations] = useState([]);
  const [sessionIds, setSessionIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const [piiReady, setPiiReady] = useState(true);

  useEffect(() => {
    // Initialize participant only once
    if (!initialized) {
      initializeParticipant();
      loadConversations();
      setInitialized(true);
    }
  }, [initialized]);

  useEffect(() => {
    if (variant === 'A') {
      checkPiiStatus();
      const interval = setInterval(checkPiiStatus, 3000);
      return () => clearInterval(interval);
    }
  }, [variant]);

  const generateLocalProlificId = () => {
    const randomPart = Math.random().toString(36).slice(2, 8);
    return `local_${Date.now()}_${randomPart}`;
  };

  const resolveProlificId = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlProlificId = urlParams.get('PROLIFIC_PID');
    if (urlProlificId) {
      localStorage.setItem(PROLIFIC_STORAGE_KEY, urlProlificId);
      return urlProlificId;
    }

    const storedId = localStorage.getItem(PROLIFIC_STORAGE_KEY);
    if (storedId) {
      return storedId;
    }

    const generatedId = generateLocalProlificId();
    localStorage.setItem(PROLIFIC_STORAGE_KEY, generatedId);
    return generatedId;
  };

  const initializeParticipant = async () => {
    try {
      // Get prolific ID from URL params if present
      const prolificId = resolveProlificId();

      const response = await axios.post(`${API_BASE_URL}/api/participants`, {
        prolific_id: prolificId
      });
      
      setParticipantId(response.data.id);
      setVariant(response.data.variant);
      setParticipantStatus(response.data.status || 'new');
      setCompletionUrl(response.data.completion_url || '');
      setProlificId(prolificId);
    } catch (error) {
      console.error('Error initializing participant:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/conversations/seed`);
      setConversations(response.data);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const checkPiiStatus = async () => {
    if (variant !== 'A') {
      setPiiReady(true);
      return;
    }
    try {
      const response = await axios.get(`${API_BASE_URL}/pii/status`);
      setPiiReady(Boolean(response.data?.loaded));
    } catch (error) {
      console.error('Error checking PII status:', error);
      setPiiReady(false);
    }
  };

  // Create sessions when participantId and conversations are available
  useEffect(() => {
    const createSessions = async () => {
      if (participantId && conversations.length > 0 && sessionIds.length === 0) {
        try {
          const sessions = await Promise.all(
            conversations.map(conv => 
              axios.post(
                `${API_BASE_URL}/api/conversations/sessions/${participantId}/${conv.conversation_id}`
              )
            )
          );
          setSessionIds(sessions.map(s => s.data.id));
        } catch (error) {
          console.error('Error creating sessions:', error);
        }
      }
    };
    createSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [participantId, conversations.length]);

  const handleConversationComplete = () => {
    if (currentConversationIndex < conversations.length - 1) {
      setCurrentConversationIndex(currentConversationIndex + 1);
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (participantStatus === 'completed') {
    return <AlreadyCompletedScreen completionUrl={completionUrl} />;
  }

  if (!participantId) {
    return <div className="error">Error initializing participant</div>;
  }

  if (variant === 'A' && !piiReady) {
    return <div className="loading">Loading PII model...</div>;
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route 
            path="/" 
            element={
              <WelcomeScreen 
                prolificId={prolificId}
                variant={variant}
              />
            } 
          />
          <Route 
            path="/conversation/:index" 
            element={
              <ConversationRoute
                conversations={conversations}
                sessionIds={sessionIds}
                participantId={participantId}
                prolificId={prolificId}
                variant={variant}
                onComplete={handleConversationComplete}
              />
            } 
          />
          <Route 
            path="/survey/:type" 
            element={
              <SurveyScreen
                participantId={participantId}
                participantProlificId={prolificId}
                variant={variant}
              />
            } 
          />
          <Route 
            path="/completion" 
            element={
              <CompletionScreen
                participantId={participantId}
                prolificId={prolificId}
              />
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
