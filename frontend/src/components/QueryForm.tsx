/**
 * QueryForm component for submitting questions
 */

import React, { useState } from 'react';

interface QueryFormProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

export const QueryForm: React.FC<QueryFormProps> = ({ onSubmit, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (query.trim()) {
      onSubmit(query.trim());
      setQuery('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="query-form">
      <div className="query-input-wrapper">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about your legal documents..."
          className="query-input"
          rows={3}
          disabled={isLoading}
          maxLength={2000}
        />
        <div className="query-form-footer">
          <span className="character-count">
            {query.length} / 2000
          </span>
          <button
            type="submit"
            className="submit-button"
            disabled={isLoading || !query.trim()}
          >
            <span>{isLoading ? 'Processing...' : 'Submit Question'}</span>
          </button>
        </div>
      </div>
    </form>
  );
};
