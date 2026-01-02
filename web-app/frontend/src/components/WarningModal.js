import React from 'react';
import './WarningModal.css';

function WarningModal({ warningState, onAcceptRewrite, onContinueAnyway }) {
  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'HIGH':
        return '#d32f2f';
      case 'MEDIUM':
        return '#ed6c02';
      case 'LOW':
        return '#0288d1';
      default:
        return '#666';
    }
  };

  return (
    <div className="warning-modal-overlay">
      <div className="warning-modal">
        <div className="warning-header">
          <div 
            className="risk-level-badge"
            style={{ backgroundColor: getRiskLevelColor(warningState.riskLevel) }}
          >
            {warningState.riskLevel} RISK
          </div>
        </div>
        
        <div className="warning-content">
          <h3>Privacy Warning</h3>
          <p className="warning-explanation">{warningState.explanation}</p>
          
          {warningState.primaryRiskFactors && warningState.primaryRiskFactors.length > 0 && (
            <div className="risk-factors">
              <strong>Primary concerns:</strong>
              <ul>
                {warningState.primaryRiskFactors.map((factor, idx) => (
                  <li key={idx}>{factor}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        <div className="warning-actions">
          <button 
            className="continue-button"
            onClick={onContinueAnyway}
          >
            Continue anyway
          </button>
          <button 
            className="accept-button"
            onClick={onAcceptRewrite}
          >
            Accept safer rewrite
          </button>
        </div>
      </div>
    </div>
  );
}

export default WarningModal;

