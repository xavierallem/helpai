/**
 * LoadingMessage component for showing AI is thinking
 */

import React from 'react';

export const LoadingMessage: React.FC = () => {
  return (
    <div className="loading-content">
      <div className="typing-indicator">
        <span className="typing-dot"></span>
        <span className="typing-dot"></span>
        <span className="typing-dot"></span>
      </div>
      <span className="thinking-text">Thinking...</span>
    </div>
  );
};
