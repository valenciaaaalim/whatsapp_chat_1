import React, { useEffect, useState, useCallback } from 'react';
import './WarningModal.css';

function WarningModal({ warningState, riskPending, riskError, capReached, onAcceptRewrite, onContinueAnyway, onRetry }) {
  const [loadingText, setLoadingText] = useState('Loading');
  const [retryCountdown, setRetryCountdown] = useState(5);
  const rewriteText = warningState?.saferRewrite || '';
  const reasoning = warningState?.reasoning || '';
  const riskLevel = warningState?.riskLevel || 'UNKNOWN';
  const disableAccept = riskPending || !rewriteText.trim();

  useEffect(() => {
    if (!riskPending) {
      setLoadingText('Loading');
      return undefined;
    }
    const frames = ['Loading', 'Loading.', 'Loading..', 'Loading...'];
    let index = 0;
    setLoadingText(frames[0]);
    const timer = setInterval(() => {
      index = (index + 1) % frames.length;
      setLoadingText(frames[index]);
    }, 450);
    return () => clearInterval(timer);
  }, [riskPending]);

  // Retry countdown when error state is active
  useEffect(() => {
    if (!riskError) {
      setRetryCountdown(5);
      return undefined;
    }
    setRetryCountdown(5);
    const timer = setInterval(() => {
      setRetryCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [riskError]);

  const handleRetry = useCallback(() => {
    if (retryCountdown > 0) return;
    if (onRetry) onRetry();
  }, [retryCountdown, onRetry]);

  // Error state — assessment failed
  if (riskError && !riskPending) {
    return (
      <div className="warning-modal-overlay">
        <div className="warning-modal">
          <div className="warning-content">
            <div className="warning-explanation" style={{ textAlign: 'center' }}>
              Unable to load the privacy assessment.
            </div>
          </div>
          <div className="warning-actions">
            <button
              className="continue-button"
              onClick={onContinueAnyway}
            >
              Continue without it
            </button>
            <button
              className="accept-button"
              onClick={handleRetry}
              disabled={retryCountdown > 0}
            >
              {retryCountdown > 0 ? `Retry (${retryCountdown})` : 'Retry'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="warning-modal-overlay">
      <div className="warning-modal">
        <div className="warning-content">
          {capReached && !riskPending && (
            <p style={{ color: '#cc0000', fontSize: '0.85em', margin: '0 0 8px 0', textAlign: 'center' }}>
              You've used all your assessments for this scenario. Please finalize your message.
            </p>
          )}
          {riskPending ? (
            <div className="warning-explanation">{loadingText}</div>
          ) : (
            <>
              <div className="risk-block">
                <h3>Risk Level</h3>
                <p className={`risk-level risk-level-${riskLevel.toLowerCase()}`}>{riskLevel}</p>
              </div>
              <div className="rewrite-block">
                <h3>Suggested Rewrite</h3>
                <div className="rewrite-text">{rewriteText || 'No rewrite available.'}</div>
              </div>
              <div className="reasoning-block">
                <h3>Reasoning</h3>
                <p className="warning-explanation">{reasoning || 'This rewrite reduces sensitive detail exposure.'}</p>
              </div>
            </>
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
            disabled={disableAccept}
          >
            Accept safer rewrite
          </button>
        </div>
      </div>
    </div>
  );
}

export default WarningModal;
