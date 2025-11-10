/**
 * API client service for Legal Document Assistant backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  Document,
  QueryRequest,
  QueryResponse,
  Session,
  HealthResponse,
  APIError,
} from '../types';

// Get API base URL from environment variable or use default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * API client class for making requests to the backend
 */
class APIClient {
  private client: AxiosInstance;

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 60000, // 60 second timeout for long operations
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<APIError>) => {
        if (error.response) {
          // Server responded with error status
          const apiError: APIError = {
            detail: error.response.data?.detail || error.message,
            status: error.response.status,
          };
          return Promise.reject(apiError);
        } else if (error.request) {
          // Request made but no response received
          const apiError: APIError = {
            detail: 'No response from server. Please check your connection.',
          };
          return Promise.reject(apiError);
        } else {
          // Error setting up the request
          const apiError: APIError = {
            detail: error.message,
          };
          return Promise.reject(apiError);
        }
      }
    );
  }

  // Health check
  async checkHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  // Document operations
  async getDocuments(): Promise<Document[]> {
    const response = await this.client.get<Document[]>('/api/documents');
    return response.data;
  }

  async uploadDocument(title: string, file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    const response = await this.client.post<Document>('/api/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getDocument(documentId: string): Promise<Document> {
    const response = await this.client.get<Document>(`/api/documents/${documentId}`);
    return response.data;
  }

  async deleteDocument(documentId: string): Promise<void> {
    await this.client.delete(`/api/documents/${documentId}`);
  }

  // Query operations
  async submitQuery(request: QueryRequest): Promise<QueryResponse> {
    const response = await this.client.post<QueryResponse>('/api/query', request);
    return response.data;
  }

  async submitQueryStream(
    request: QueryRequest,
    onToken: (token: string) => void,
    onSources: (sources: any[]) => void,
    onDone: (sessionId: string, processingTime: number) => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${this.client.defaults.baseURL}/api/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'sources':
                  onSources(data.sources);
                  break;
                case 'token':
                  onToken(data.content);
                  break;
                case 'done':
                  onDone(data.session_id, data.processing_time_ms);
                  break;
                case 'error':
                  onError(data.error);
                  break;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error: any) {
      onError(error.message || 'Failed to stream query');
    }
  }

  // Session operations
  async getSession(sessionId: string): Promise<Session> {
    const response = await this.client.get<Session>(`/api/sessions/${sessionId}`);
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.client.delete(`/api/sessions/${sessionId}`);
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export class for testing
export { APIClient };
