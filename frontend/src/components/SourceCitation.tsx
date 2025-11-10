/**
 * SourceCitation component for displaying source documents
 */

import React, { useState } from 'react';
import { SourceDocument } from '../types';

interface SourceCitationProps {
  sources: SourceDocument[];
}

export const SourceCitation: React.FC<SourceCitationProps> = ({ sources }) => {
  const [expanded, setExpanded] = useState(false);

  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="source-citation">
      <button
        className="source-toggle"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? '▼' : '▶'} Sources ({sources.length})
      </button>

      {expanded && (
        <div className="source-list">
          {sources.map((source, index) => (
            <div key={source.chunk_id} className="source-item">
              <div className="source-header">
                <span className="source-number">Source {index + 1}</span>
                <span className="source-metadata">
                  {source.page_number && `Page ${source.page_number} • `}
                  Relevance: {(source.similarity_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="source-content">
                {source.content}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
