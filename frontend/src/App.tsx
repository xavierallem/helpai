/**
 * Main App component for Legal Document Assistant
 */

import { useState, useEffect, useRef } from 'react';
import { QueryClient, QueryClientProvider, useMutation, useQuery } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { apiClient } from './services/api';
import { QueryForm } from './components/QueryForm';
import { ResponseDisplay, Message } from './components/ResponseDisplay';
import { LoadingMessage } from './components/LoadingMessage';
import { DocumentUpload } from './components/DocumentUpload';
import { DocumentList } from './components/DocumentList';
import { APIError, Document, SourceDocument } from './types';
import './App.css';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

/**
 * Main query interface component
 */
function QueryInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleSubmitQuery = async (queryText: string) => {
    // Add question to messages
    setMessages((prev) => [
      ...prev,
      {
        type: 'question',
        content: queryText,
      },
    ]);

    // Reset streaming state
    setIsStreaming(true);
    setStreamingContent('');

    // Accumulate the full response
    let fullResponse = '';
    let finalSources: SourceDocument[] = [];

    // Submit streaming query
    await apiClient.submitQueryStream(
      {
        query_text: queryText,
        session_id: sessionId,
      },
      // onToken
      (token: string) => {
        fullResponse += token;
        setStreamingContent(fullResponse);
      },
      // onSources
      (sources: any[]) => {
        finalSources = sources.map(s => ({
          document_id: s.document_id,
          chunk_id: s.chunk_id,
          content: s.content,
          page_number: s.page_number,
          similarity_score: s.similarity_score,
        }));
      },
      // onDone
      (newSessionId: string, processingTime: number) => {
        setSessionId(newSessionId);
        setMessages((prev) => [
          ...prev,
          {
            type: 'answer',
            content: fullResponse,
            sources: finalSources,
            processingTime,
          },
        ]);
        setIsStreaming(false);
        setStreamingContent('');
      },
      // onError
      (error: string) => {
        setMessages((prev) => [
          ...prev,
          {
            type: 'answer',
            content: `Error: ${error}`,
          },
        ]);
        setIsStreaming(false);
        setStreamingContent('');
      }
    );
  };

  return (
    <div className="query-interface">
      <div className="messages-container">
        <ResponseDisplay messages={messages} />
        {isStreaming && (
          <div className="message answer streaming">
            <div className="message-header">
              <span className="message-label">Assistant</span>
              <span className="streaming-indicator">●</span>
            </div>
            <div className="message-content markdown-content">
              {streamingContent ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {streamingContent}
                </ReactMarkdown>
              ) : (
                <LoadingMessage />
              )}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="query-form-container">
        <QueryForm
          onSubmit={handleSubmitQuery}
          isLoading={isStreaming}
        />
      </div>
    </div>
  );
}

/**
 * Document management interface component
 */
function DocumentInterface() {
  // Query for fetching documents
  const { data: documents = [], refetch } = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: async () => await apiClient.getDocuments(),
  });

  // Mutation for uploading documents
  const uploadMutation = useMutation({
    mutationFn: async ({ title, file }: { title: string; file: File }) => {
      return await apiClient.uploadDocument(title, file);
    },
    onSuccess: () => {
      refetch();
    },
    onError: (error: APIError) => {
      alert(`Upload failed: ${error.detail}`);
    },
  });

  // Mutation for deleting documents
  const deleteMutation = useMutation({
    mutationFn: async (documentId: string) => {
      return await apiClient.deleteDocument(documentId);
    },
    onSuccess: () => {
      refetch();
    },
    onError: (error: APIError) => {
      alert(`Delete failed: ${error.detail}`);
    },
  });

  const handleUpload = (title: string, file: File) => {
    uploadMutation.mutate({ title, file });
  };

  const handleDelete = (documentId: string) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      deleteMutation.mutate(documentId);
    }
  };

  return (
    <div className="document-interface">
      <div className="document-section">
        <h2 className="section-title">Upload Document</h2>
        <DocumentUpload
          onUpload={handleUpload}
          onUploadSuccess={() => refetch()}
          isUploading={uploadMutation.isPending}
        />
      </div>
      <div className="document-section">
        <DocumentList
          documents={documents}
          onDelete={handleDelete}
          isDeleting={deleteMutation.isPending}
        />
      </div>
    </div>
  );
}

/**
 * Main application component
 */
function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="app">
        <header className="app-header">
          <h1>Legal Document Assistant</h1>
          <p className="app-subtitle">Ask questions about your legal documents</p>
        </header>
        <nav className="app-nav">
          <button
            className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            💬 Chat
          </button>
          <button
            className={`nav-tab ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            📄 Documents
          </button>
        </nav>
        <main className="app-main">
          {activeTab === 'chat' ? <QueryInterface /> : <DocumentInterface />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
