import React from 'react';
import './MessageBubble.css';

function MessageBubble({ message }) {
  const isSent = message.direction === 'SENT';
  
  const formatTime = (date) => {
    const d = new Date(date);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`message-bubble-wrapper ${isSent ? 'sent' : 'received'}`}>
      <div className={`message-bubble ${isSent ? 'sent' : 'received'}`}>
        <div className="message-text">{message.text}</div>
        <div className="message-time">{formatTime(message.timestamp)}</div>
      </div>
    </div>
  );
}

export default MessageBubble;

