import React from 'react';
import './ChatComposer.css';

function ChatComposer({ draftText, onTextChange, onSend }) {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="chat-composer">
      <div className="composer-content">
        <textarea
          className="message-input"
          placeholder="Type a message"
          value={draftText}
          onChange={(e) => onTextChange(e.target.value)}
          onKeyPress={handleKeyPress}
          rows={1}
        />
        <button
          className="send-button"
          onClick={onSend}
          disabled={!draftText.trim()}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"
              fill="currentColor"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default ChatComposer;

