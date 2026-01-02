import React from 'react';
import './DateSeparator.css';

function DateSeparator({ date }) {
  return (
    <div className="date-separator">
      <span className="date-separator-text">{date}</span>
    </div>
  );
}

export default DateSeparator;

