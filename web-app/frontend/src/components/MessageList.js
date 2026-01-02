import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import DateSeparator from './DateSeparator';
import './MessageList.css';

function MessageList({ messages }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatDate = (date) => {
    const today = new Date();
    const messageDate = new Date(date);
    const diffTime = Math.abs(today - messageDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
      return 'Today';
    } else if (diffDays === 2) {
      return 'Yesterday';
    } else {
      return messageDate.toLocaleDateString();
    }
  };

  const needsDateSeparator = (prevDate, currentDate) => {
    if (!prevDate) return true;
    const prev = new Date(prevDate);
    const curr = new Date(currentDate);
    return prev.toDateString() !== curr.toDateString();
  };

  return (
    <div className="message-list">
      {messages.map((message, index) => {
        const prevMessage = index > 0 ? messages[index - 1] : null;
        const showSeparator = needsDateSeparator(
          prevMessage?.timestamp,
          message.timestamp
        );

        return (
          <React.Fragment key={message.id}>
            {showSeparator && (
              <DateSeparator date={formatDate(message.timestamp)} />
            )}
            <MessageBubble message={message} />
          </React.Fragment>
        );
      })}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default MessageList;

