import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import ChatComposer from './ChatComposer';
import WarningModal from './WarningModal';
import './ConversationScreen.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function ConversationScreen({ conversation, sessionId, participantId, variant, onComplete, conversationIndex }) {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [draftText, setDraftText] = useState('');
  const [warningState, setWarningState] = useState(null);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [preClickText, setPreClickText] = useState('');
  const typingTimeoutRef = useRef(null);

  useEffect(() => {
    // Initialize messages from conversation data
    // Show only received messages initially (contact's messages)
    const allMessages = conversation.conversation || [];
    const initialMessages = allMessages
      .filter(msg => msg.direction === 'RECEIVED')
      .map((msg, idx) => ({
        ...msg,
        timestamp: new Date(Date.now() - (allMessages.length - idx) * 60000)
      }));
    setMessages(initialMessages);
    
    // Set message index to track where we are in the conversation
    setCurrentMessageIndex(initialMessages.length);
  }, [conversation]);

  const handleTyping = (text) => {
    setDraftText(text);
    setPreClickText(text); // Capture pre-click text
    
    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // Debounce risk assessment
    if (text.trim()) {
      typingTimeoutRef.current = setTimeout(() => {
        assessRisk(text);
      }, 1500);
    } else {
      setWarningState(null);
    }
  };

  const assessRisk = async (text) => {
    try {
      const conversationHistory = messages.map(m => m.text);
      const response = await axios.post(`${API_BASE_URL}/api/risk/assess`, {
        draft_text: text,
        conversation_history: conversationHistory,
        session_id: sessionId
      });
      
      if (response.data.show_warning && 
          (response.data.risk_level === 'MEDIUM' || response.data.risk_level === 'HIGH')) {
        setWarningState({
          riskLevel: response.data.risk_level,
          explanation: response.data.explanation,
          saferRewrite: response.data.safer_rewrite,
          primaryRiskFactors: response.data.primary_risk_factors
        });
      } else {
        setWarningState(null);
      }
    } catch (error) {
      console.error('Error assessing risk:', error);
    }
  };

  const handleSend = async () => {
    if (!draftText.trim()) return;
    
    const finalText = draftText.trim();
    
    // Capture user input
    try {
      if (warningState) {
        await axios.post(`${API_BASE_URL}/api/user-inputs/with-warning`, {
          session_id: sessionId,
          message_index: currentMessageIndex,
          action_type: 'ignore',
          pre_click_text: preClickText,
          final_submitted_text: finalText,
          risk_level: warningState.riskLevel,
          warning_explanation: warningState.explanation,
          safer_rewrite_offered: warningState.saferRewrite
        });
      } else {
        await axios.post(`${API_BASE_URL}/api/user-inputs`, {
          session_id: sessionId,
          message_index: currentMessageIndex,
          action_type: 'none',
          pre_click_text: preClickText,
          final_submitted_text: finalText
        });
      }
    } catch (error) {
      console.error('Error capturing user input:', error);
    }
    
    // Add message to list
    const newMessage = {
      id: `sent-${Date.now()}`,
      text: finalText,
      direction: 'SENT',
      timestamp: new Date()
    };
    
    setMessages([...messages, newMessage]);
    setDraftText('');
    setWarningState(null);
    setCurrentMessageIndex(currentMessageIndex + 1);
    
    // Show next received message if available (simulate conversation flow)
    // In a real scenario, we'd check if there are more messages in the conversation
    const allMessages = conversation.conversation || [];
    const currentReceivedCount = messages.filter(m => m.direction === 'RECEIVED').length;
    const totalReceivedMessages = allMessages.filter(m => m.direction === 'RECEIVED').length;
    
    if (currentReceivedCount < totalReceivedMessages) {
      // Find next received message
      const nextReceived = allMessages
        .slice(currentReceivedCount * 2) // Skip past pairs of sent/received
        .find(msg => msg.direction === 'RECEIVED');
      
      if (nextReceived) {
        setTimeout(() => {
          const nextMessage = {
            ...nextReceived,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, nextMessage]);
          setCurrentMessageIndex(prev => prev + 1);
        }, 1000);
      }
    } else {
      // Conversation complete - wait a bit then show survey
      setTimeout(() => {
        onComplete();
        navigate(`/survey/mid?index=${conversationIndex}`);
      }, 2000);
    }
  };

  const handleAcceptRewrite = () => {
    if (warningState) {
      setDraftText(warningState.saferRewrite);
      setWarningState(null);
    }
  };

  const handleContinueAnyway = async () => {
    setWarningState(null);
    // User continues with original text, which will be captured on send
  };

  // Get contact name from conversation data (first received message's name)
  const getContactName = () => {
    const convData = conversation.conversation || [];
    const firstReceived = convData.find(m => m.direction === 'RECEIVED');
    return firstReceived?.name || 'Contact';
  };
  
  const contactName = getContactName();

  return (
    <div className="conversation-screen">
      <ChatHeader contactName={contactName} scenario={conversation.scenario} />
      <MessageList messages={messages} />
      <ChatComposer
        draftText={draftText}
        onTextChange={handleTyping}
        onSend={handleSend}
      />
      {warningState && (
        <WarningModal
          warningState={warningState}
          onAcceptRewrite={handleAcceptRewrite}
          onContinueAnyway={handleContinueAnyway}
        />
      )}
    </div>
  );
}

export default ConversationScreen;

