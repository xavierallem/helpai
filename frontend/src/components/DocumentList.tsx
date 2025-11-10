/**
 * DocumentList component for displaying uploaded documents
 */

import React from 'react';
import { Document } from '../types';

interface DocumentListProps {
  documents: Document[];
  onDelete: (documentId: string) => void;
  isDeleting: boolean;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onDelete,
  isDeleting,
}) => {
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      pending: 'status-badge status-pending',
      processing: 'status-badge status-processing',
      completed: 'status-badge status-completed',
      failed: 'status-badge status-failed',
    };

    const statusLabels = {
      pending: 'Pending',
      processing: 'Processing',
      completed: 'Ready',
      failed: 'Failed',
    };

    return (
      <span className={statusClasses[status as keyof typeof statusClasses] || 'status-badge'}>
        {statusLabels[status as keyof typeof statusLabels] || status}
      </span>
    );
  };

  if (documents.length === 0) {
    return (
      <div className="document-list empty">
        <p className="empty-message">
          No documents uploaded yet. Upload a PDF to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="document-list">
      <h3 className="document-list-title">Uploaded Documents ({documents.length})</h3>
      <div className="document-items">
        {documents.map((doc) => (
          <div key={doc.document_id} className="document-item">
            <div className="document-icon">📄</div>
            <div className="document-details">
              <div className="document-header">
                <h4 className="document-title">{doc.title}</h4>
                {getStatusBadge(doc.processing_status)}
              </div>
              <div className="document-meta">
                <span className="meta-item">
                  {formatFileSize(doc.file_size_bytes)}
                </span>
                {doc.total_chunks > 0 && (
                  <span className="meta-item">{doc.total_chunks} chunks</span>
                )}
                <span className="meta-item">
                  Uploaded {formatDate(doc.uploaded_at)}
                </span>
              </div>
            </div>
            <button
              className="delete-button"
              onClick={() => onDelete(doc.document_id)}
              disabled={isDeleting}
              title="Delete document"
            >
              🗑️
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
