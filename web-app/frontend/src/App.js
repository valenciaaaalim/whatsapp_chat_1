import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import WelcomeScreen from './components/WelcomeScreen';
import ConversationScreen from './components/ConversationScreen';
import SurveyScreen from './components/SurveyScreen';
import CompletionScreen from './components/CompletionScreen';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [participantId, setParticipantId] = useState(null);
  const [variant, setVariant] = useState(null);
  const [currentConversationIndex, setCurrentConversationIndex] = useState(0);
  const [conversations, setConversations] = useState([]);
  const [sessionIds, setSessionIds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize participant
    initializeParticipant();
    loadConversations();
  }, []);

  const initializeParticipant = async () => {
    try {
      // Get prolific ID from URL params if present
      const urlParams = new URLSearchParams(window.location.search);
      const prolificId = urlParams.get('PROLIFIC_PID') || null;

      const response = await axios.post(`${API_BASE_URL}/api/participants`, {
        prolific_id: prolificId
      });
      
      setParticipantId(response.data.id);
      setVariant(response.data.variant);
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
      
      // Create sessions for all conversations
      if (participantId) {
        const sessions = await Promise.all(
          response.data.map(conv => 
            axios.post(
              `${API_BASE_URL}/api/conversations/sessions/${participantId}/${conv.conversation_id}`
            )
          )
        );
        setSessionIds(sessions.map(s => s.data.id));
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const handleConversationComplete = () => {
    if (currentConversationIndex < conversations.length - 1) {
      setCurrentConversationIndex(currentConversationIndex + 1);
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!participantId) {
    return <div className="error">Error initializing participant</div>;
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route 
            path="/" 
            element={
              <WelcomeScreen 
                participantId={participantId}
                variant={variant}
              />
            } 
          />
          <Route 
            path="/conversation/:index" 
            element={
              currentConversationIndex < conversations.length ? (
                <ConversationScreen
                  conversation={conversations[currentConversationIndex]}
                  sessionId={sessionIds[currentConversationIndex]}
                  participantId={participantId}
                  variant={variant}
                  onComplete={handleConversationComplete}
                  conversationIndex={currentConversationIndex}
                />
              ) : (
                <Navigate to="/completion" />
              )
            } 
          />
          <Route 
            path="/survey/:type" 
            element={
              <SurveyScreen
                participantId={participantId}
              />
            } 
          />
          <Route 
            path="/completion" 
            element={
              <CompletionScreen
                participantId={participantId}
              />
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

