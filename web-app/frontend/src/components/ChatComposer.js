import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './ChatComposer.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function ChatComposer({ draftText, onTextChange, onSend, variant }) {
  const [piiSpans, setPiiSpans] = useState([]);
  const [maskedText, setMaskedText] = useState('');
  const debounceTimeoutRef = useRef(null);
  const requestCounterRef = useRef(0);
  const textareaRef = useRef(null);
  const overlayRef = useRef(null);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  // PII detection for Group A only
  useEffect(() => {
    // Only enable PII detection for Group A
    if (variant !== 'A') {
      setPiiSpans([]);
      setMaskedText('');
      return;
    }

    // Clear previous timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // If text is empty, clear PII spans
    if (!draftText.trim()) {
      setPiiSpans([]);
      setMaskedText('');
      return;
    }

    // Debounce PII detection (1500ms)
    debounceTimeoutRef.current = setTimeout(() => {
      const currentRequest = ++requestCounterRef.current;
      console.log('[PII] debounce fired', { length: draftText.length, request: currentRequest });
      
      axios.post(
        `${API_BASE_URL}/pii/detect`,
        { draft_text: draftText },
        { timeout: 30000 }
      )
      .then(response => {
        // Ignore stale responses
        if (currentRequest === requestCounterRef.current) {
          console.log('[PII] detect success', {
            request: currentRequest,
            spans: response.data?.pii_spans?.length || 0
          });
          setPiiSpans(response.data.pii_spans || []);
          setMaskedText(response.data.masked_text || '');
        }
      })
      .catch(error => {
        console.error('[PII] detect error', error);
        // Ignore stale responses
        if (currentRequest === requestCounterRef.current) {
          setPiiSpans([]);
          setMaskedText('');
        }
      });
    }, 1500);

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [draftText, variant]);

  // Sync scroll between textarea and overlay
  const handleScroll = () => {
    if (overlayRef.current && textareaRef.current) {
      overlayRef.current.scrollTop = textareaRef.current.scrollTop;
      overlayRef.current.scrollLeft = textareaRef.current.scrollLeft;
    }
  };

  // Render text with PII underlines for overlay
  const renderOverlayText = () => {
    if (piiSpans.length === 0) {
      return draftText;
    }

    // Sort spans by start position
    const sortedSpans = [...piiSpans].sort((a, b) => a.start - b.start);
    const parts = [];
    let lastIndex = 0;

    sortedSpans.forEach((span, idx) => {
      // Add text before span
      if (span.start > lastIndex) {
        parts.push({
          text: draftText.substring(lastIndex, span.start),
          isPii: false,
          key: `before-${idx}`
        });
      }
      // Add PII span
      parts.push({
        text: draftText.substring(span.start, span.end),
        isPii: true,
        key: `pii-${idx}`
      });
      lastIndex = span.end;
    });

    // Add remaining text
    if (lastIndex < draftText.length) {
      parts.push({
        text: draftText.substring(lastIndex),
        isPii: false,
        key: 'after'
      });
    }

    return parts.map(part => (
      <span key={part.key} className={part.isPii ? 'pii-underline' : ''}>
        {part.text}
      </span>
    ));
  };

  return (
    <div className="chat-composer">
      <div className="composer-content">
        <div className="textarea-wrapper">
          {/* PII Underline Overlay (Group A only) */}
          {variant === 'A' && (
            <div
              ref={overlayRef}
              className="pii-overlay"
              aria-hidden="true"
            >
              {renderOverlayText()}
            </div>
          )}
          <textarea
            ref={textareaRef}
            className="message-input"
            placeholder="Type a message"
            value={draftText}
            onChange={(e) => onTextChange(e.target.value)}
            onKeyPress={handleKeyPress}
            onScroll={handleScroll}
            rows={1}
          />
        </div>
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
