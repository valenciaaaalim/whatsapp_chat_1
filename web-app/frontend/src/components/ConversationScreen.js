import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import ChatComposer from './ChatComposer';
import WarningModal from './WarningModal';
import './ConversationScreen.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function ConversationScreen({ conversation, sessionId, participantId, participantProlificId, variant, onComplete, conversationIndex }) {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [draftText, setDraftText] = useState('');
  const [warningState, setWarningState] = useState(null);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [preClickText, setPreClickText] = useState('');
  const [lastOfferedRewrite, setLastOfferedRewrite] = useState(null); // Track last offered rewrite for Group A
  const typingTimeoutRef = useRef(null);

  useEffect(() => {
    // Initialize messages from conversation data
    // Show all messages with proper directions from the JSON
    // Messages alternate: contact (RECEIVED) -> user (SENT) -> contact (RECEIVED) -> etc.
    const allMessages = conversation.conversation || [];
    
    // Show all messages with their correct directions
    // Pre-existing user messages (SENT) from JSON will be shown as green bubbles on right
    // Contact messages (RECEIVED) will be shown as white bubbles on left
    const initialMessages = allMessages.map((msg, idx) => ({
      ...msg,
      timestamp: new Date(Date.now() - (allMessages.length - idx) * 60000)
    }));
    
    setMessages(initialMessages);
    
    // Set message index to track where we are (all messages are already shown)
    setCurrentMessageIndex(allMessages.length);
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
      }, 1000);
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
        const rewrite = response.data.safer_rewrite;
        setWarningState({
          riskLevel: response.data.risk_level,
          explanation: response.data.explanation,
          saferRewrite: rewrite,
          primaryRiskFactors: response.data.primary_risk_factors
        });
        // Track offered rewrite for Group A
        if (variant === 'A' && rewrite) {
          setLastOfferedRewrite(rewrite);
        }
      } else {
        setWarningState(null);
        setLastOfferedRewrite(null);
      }
    } catch (error) {
      console.error('Error assessing risk:', error);
    }
  };

  const handleSend = async () => {
    if (!draftText.trim()) return;
    
    const finalText = draftText.trim();
    console.log('[Send] clicked', { variant, length: finalText.length });
    
    // For Group A: Get PII detection results and determine rewrite status
    let finalRawText = null;
    let finalMaskedText = null;
    let finalRewriteText = null;
    
    if (variant === 'A') {
      finalRawText = preClickText || draftText.trim(); // Use pre-click text if available, otherwise current draft
      
      // Get PII masked text
      try {
        const piiResponse = await axios.post(
          `${API_BASE_URL}/pii/detect`,
          { draft_text: finalRawText },
          { timeout: 30000 }
        );
        finalMaskedText = piiResponse.data.masked_text || null;
        console.log('[PII] detect for storage success', {
          spans: piiResponse.data?.pii_spans?.length || 0
        });
      } catch (error) {
        console.error('[PII] detect for storage error', error);
      }
      
      // Determine rewrite status
      if (lastOfferedRewrite) {
        // Check if rewrite was accepted (finalText matches the rewrite)
        if (finalText === lastOfferedRewrite.trim()) {
          finalRewriteText = lastOfferedRewrite; // Rewrite was accepted
        } else {
          finalRewriteText = 'Rewrite'; // Rewrite was offered but ignored
        }
      }
    }
    
    // Capture user input
    try {
      const messagePayload = {
        participant_id: participantProlificId,
        conversation_index: conversationIndex,
        final_message: finalText,
        variant
      };
      
      // Add Group A PII fields
      if (variant === 'A') {
        messagePayload.final_raw_text = finalRawText;
        messagePayload.final_masked_text = finalMaskedText;
        if (finalRewriteText) {
          messagePayload.final_rewrite_text = finalRewriteText;
        }
      }
      
      await axios.post(`${API_BASE_URL}/api/participant-records/message`, messagePayload);

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
      console.error('[Send] error capturing user input', error);
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
    setLastOfferedRewrite(null); // Reset rewrite tracking
    setCurrentMessageIndex(currentMessageIndex + 1);
    
    // Since we're showing all messages from the start, 
    // user typing new messages means they're continuing the conversation
    // Check if we should show completion or allow more messages
    const allMessages = conversation.conversation || [];
    const userTypedMessages = messages.filter(m => m.id && m.id.startsWith('sent-')).length;
    
    // If user has typed a few messages, consider conversation complete
    // Or check if we've reached the end of the conversation flow
    if (userTypedMessages > 0 || currentMessageIndex >= allMessages.length) {
      // Conversation complete - wait a bit then show survey
      setTimeout(() => {
        onComplete();
        navigate(`/survey/mid?index=${conversationIndex}`);
      }, 2000);
    }
  };

  const handleAcceptRewrite = () => {
    if (warningState && warningState.saferRewrite) {
      setDraftText(warningState.saferRewrite);
      // Keep lastOfferedRewrite so we can track that it was accepted on send
      setWarningState(null);
    }
  };

  const handleContinueAnyway = async () => {
    setWarningState(null);
    // Keep lastOfferedRewrite so we can track that rewrite was offered but ignored
    // User continues with original text, which will be captured on send
  };

  // Get contact name from conversation data (first received message's name)
  const getContactName = () => {
    const convData = conversation.conversation || [];
    const firstReceived = convData.find(m => m.direction === 'RECEIVED');
    const fullName = firstReceived?.name || 'Contact';
    // Remove occupation description (everything after " - " or " | ")
    const nameOnly = fullName.split(' - ')[0].split(' | ')[0].trim();
    return nameOnly;
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
        variant={variant}
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
