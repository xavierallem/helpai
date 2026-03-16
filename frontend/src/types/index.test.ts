import { describe, it, expect } from 'vitest';
import type { Document, QueryRequest, QueryResponse, SourceDocument } from './index';

describe('Type shapes', () => {
  it('Document object has required fields', () => {
    const doc: Document = {
      document_id: 'abc-123',
      title: 'Contract',
      processing_status: 'completed',
      uploaded_at: '2026-01-01T00:00:00Z',
      total_chunks: 5,
      file_size_bytes: 1024,
    };
    expect(doc.document_id).toBe('abc-123');
    expect(doc.processing_status).toBe('completed');
    expect(doc.processed_at).toBeUndefined();
  });

  it('QueryRequest can omit session_id', () => {
    const req: QueryRequest = { query_text: 'What is this clause?' };
    expect(req.session_id).toBeUndefined();
  });

  it('QueryRequest accepts session_id', () => {
    const req: QueryRequest = {
      query_text: 'Explain indemnification',
      session_id: 'session-abc',
    };
    expect(req.session_id).toBe('session-abc');
  });

  it('SourceDocument has similarity_score between 0 and 1', () => {
    const src: SourceDocument = {
      document_id: 'doc-1',
      chunk_id: 'chunk-1',
      content: 'Some legal text',
      similarity_score: 0.92,
    };
    expect(src.similarity_score).toBeGreaterThanOrEqual(0);
    expect(src.similarity_score).toBeLessThanOrEqual(1);
  });

  it('QueryResponse has all required fields', () => {
    const res: QueryResponse = {
      response_text: 'The clause states...',
      source_documents: [],
      session_id: 'session-1',
      processing_time_ms: 340,
    };
    expect(res.source_documents).toHaveLength(0);
    expect(res.processing_time_ms).toBeGreaterThan(0);
  });

  it('ProcessingStatus accepts valid values', () => {
    const statuses = ['pending', 'processing', 'completed', 'failed'] as const;
    statuses.forEach((s) => {
      const doc: Document = {
        document_id: 'x',
        title: 'Doc',
        processing_status: s,
        uploaded_at: '',
        total_chunks: 0,
        file_size_bytes: 0,
      };
      expect(doc.processing_status).toBe(s);
    });
  });
});
