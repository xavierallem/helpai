/**
 * TypeScript type definitions for Legal Document Assistant
 */

// Processing status enum
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

// Document types
export interface Document {
  document_id: string;
  title: string;
  processing_status: ProcessingStatus;
  uploaded_at: string;
  processed_at?: string;
  total_chunks: number;
  file_size_bytes: number;
}

export interface DocumentUploadRequest {
  title: string;
  file: File;
}

// Query types
export interface SourceDocument {
  document_id: string;
  chunk_id: string;
  content: string;
  page_number?: number;
  similarity_score: number;
}

export interface QueryRequest {
  query_text: string;
  session_id?: string;
}

export interface QueryResponse {
  response_text: string;
  source_documents: SourceDocument[];
  session_id: string;
  processing_time_ms: number;
}

// Session types
export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Session {
  session_id: string;
  message_count: number;
  created_at: string;
  last_activity: string;
}

// Health check types
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  components?: {
    chromadb: {
      status: string;
      total_chunks: number;
      collection_name: string;
      embedding_model: string;
    };
    sessions: {
      status: string;
      active_sessions: number;
      timeout_minutes: number;
    };
  };
  error?: string;
}

// API Error types
export interface APIError {
  detail: string;
  status?: number;
}
