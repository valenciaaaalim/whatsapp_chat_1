import React from 'react';
import './ChatHeader.css';

function ChatHeader({ contactName, scenario }) {
  return (
    <div className="chat-header">
      <div className="chat-header-content">
        <div className="back-arrow">←</div>
        <div className="profile-picture">
          {contactName.charAt(0).toUpperCase()}
        </div>
        <div className="contact-info">
          <div className="contact-name">{contactName}</div>
          <div className="scenario-badge">{scenario}</div>
        </div>
      </div>
    </div>
  );
}

export default ChatHeader;

