/**
 * DocumentUpload component for uploading PDF documents
 */

import React, { useState } from 'react';

interface DocumentUploadProps {
  onUploadSuccess: () => void;
  isUploading: boolean;
  onUpload: (title: string, file: File) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onUpload,
  isUploading,
}) => {
  const [title, setTitle] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);

      // Auto-fill title from filename if empty
      if (!title) {
        const filename = file.name.replace(/\.pdf$/i, '');
        setTitle(filename);
      }
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        setSelectedFile(file);

        // Auto-fill title from filename if empty
        if (!title) {
          const filename = file.name.replace(/\.pdf$/i, '');
          setTitle(filename);
        }
      } else {
        alert('Please upload a PDF file');
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile || !title.trim()) {
      return;
    }

    onUpload(title.trim(), selectedFile);

    // Reset form
    setTitle('');
    setSelectedFile(null);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="document-upload">
      <form onSubmit={handleSubmit}>
        <div className="upload-section">
          <div
            className={`file-drop-zone ${dragActive ? 'active' : ''} ${
              selectedFile ? 'has-file' : ''
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {!selectedFile ? (
              <>
                <div className="drop-icon">📄</div>
                <p className="drop-text">
                  Drag and drop a PDF file here, or click to select
                </p>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="file-input"
                  disabled={isUploading}
                />
              </>
            ) : (
              <div className="selected-file">
                <div className="file-icon">📄</div>
                <div className="file-info">
                  <div className="file-name">{selectedFile.name}</div>
                  <div className="file-size">
                    {formatFileSize(selectedFile.size)}
                  </div>
                </div>
                <button
                  type="button"
                  className="remove-file-button"
                  onClick={() => setSelectedFile(null)}
                  disabled={isUploading}
                >
                  ✕
                </button>
              </div>
            )}
          </div>

          <div className="title-input-wrapper">
            <label htmlFor="document-title">Document Title</label>
            <input
              id="document-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter document title..."
              className="title-input"
              disabled={isUploading}
              maxLength={500}
            />
          </div>

          <button
            type="submit"
            className="upload-button"
            disabled={isUploading || !selectedFile || !title.trim()}
          >
            {isUploading ? 'Uploading...' : 'Upload Document'}
          </button>
        </div>
      </form>
    </div>
  );
};
