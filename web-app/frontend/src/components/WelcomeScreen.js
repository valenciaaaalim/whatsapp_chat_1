import React from 'react';
import { useNavigate } from 'react-router-dom';
import './WelcomeScreen.css';

function WelcomeScreen({ participantId, variant }) {
  const navigate = useNavigate();

  const handleStart = () => {
    navigate('/survey/pre');
  };

  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <h1>Welcome to the WhatsApp Risk Assessment Study</h1>
        <p>
          Thank you for participating in this research study. You will be asked to 
          interact with simulated WhatsApp conversations and make decisions about 
          messaging privacy.
        </p>
        <div className="welcome-instructions">
          <h2>Instructions</h2>
          <ul>
            <li>You will see three different conversation scenarios</li>
            <li>For each scenario, you can type responses as you would in a normal chat</li>
            <li>The system may show warnings about privacy risks</li>
            <li>You can choose to accept safer suggestions or continue with your original message</li>
            <li>After each conversation, you'll answer a few survey questions</li>
          </ul>
        </div>
        <button className="start-button" onClick={handleStart}>
          Start Study
        </button>
        <p className="variant-info">Participant ID: {participantId} | Variant: {variant}</p>
      </div>
    </div>
  );
}

export default WelcomeScreen;

