/**
 * ResponseDisplay component for showing Q&A conversation
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { QueryResponse } from '../types';
import { SourceCitation } from './SourceCitation';

interface Message {
  type: 'question' | 'answer';
  content: string;
  sources?: QueryResponse['source_documents'];
  processingTime?: number;
}

interface ResponseDisplayProps {
  messages: Message[];
}

export const ResponseDisplay: React.FC<ResponseDisplayProps> = ({ messages }) => {
  if (messages.length === 0) {
    return (
      <div className="response-display empty">
        <p className="empty-message">
          No conversation yet. Ask a question to get started!
        </p>
      </div>
    );
  }

  return (
    <div className="response-display">
      {messages.map((message, index) => (
        <div
          key={index}
          className={`message ${message.type === 'question' ? 'question' : 'answer'}`}
        >
          <div className="message-header">
            <span className="message-label">
              {message.type === 'question' ? 'You' : 'Assistant'}
            </span>
            {message.processingTime && (
              <span className="processing-time">
                {message.processingTime.toFixed(0)}ms
              </span>
            )}
          </div>
          <div className="message-content markdown-content">
            {message.type === 'answer' ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            ) : (
              message.content
            )}
          </div>
          {message.sources && message.sources.length > 0 && (
            <div className="message-sources">
              <SourceCitation sources={message.sources} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export type { Message };
