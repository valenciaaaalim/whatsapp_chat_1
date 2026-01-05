import React, { useEffect } from 'react';
import './AlreadyCompletedScreen.css';

function AlreadyCompletedScreen({ completionUrl }) {
  useEffect(() => {
    if (!completionUrl) return;
    const timer = setTimeout(() => {
      window.location.href = completionUrl;
    }, 2000);
    return () => clearTimeout(timer);
  }, [completionUrl]);

  return (
    <div className="already-completed-screen">
      <div className="already-completed-content">
        <h1>Study Already Completed</h1>
        <p>
          Our records show you have already completed this study.
        </p>
        <p>
          You will be redirected back to Prolific shortly.
        </p>
        {completionUrl && (
          <button
            className="already-completed-button"
            onClick={() => { window.location.href = completionUrl; }}
          >
            Return to Prolific
          </button>
        )}
      </div>
    </div>
  );
}

export default AlreadyCompletedScreen;
