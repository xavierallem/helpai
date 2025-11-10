# Legal Document Assistant

A text-based legal document Q&A system using RAG (Retrieval-Augmented Generation) with local LLM inference.

## Features

- **Document Upload**: Upload PDF legal documents (drag-and-drop supported)
- **Intelligent Q&A**: Ask questions and get answers based on your documents
- **Source Citations**: Every answer includes references to source documents
- **Conversation Context**: Maintains conversation history within sessions
- **Local & Private**: All processing happens locally using Ollama
- **Real-time Status**: See document processing status in real-time

## Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- Ollama (local LLM inference)
- ChromaDB (vector database)
- LangChain (RAG orchestration)
- sentence-transformers (embeddings)
- PyMuPDF (PDF processing)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TanStack Query (state management)
- Axios (HTTP client)

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama

### Installation

1. **Install and start Ollama:**
   ```bash
   # Install Ollama (see https://ollama.com)
   curl -fsSL https://ollama.com/install.sh | sh  # Linux
   # or brew install ollama  # macOS

   # Start Ollama
   ollama serve

   # Pull model
   ollama pull llama3.2:3b
   ```

2. **Setup Backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. **Setup Frontend:**
   ```bash
   cd frontend
   npm install
   cp .env.example .env
   ```

4. **Start Application:**

   Terminal 1 - Backend:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Terminal 2 - Frontend:
   ```bash
   cd frontend
   npm run dev
   ```

5. **Access Application:**
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Usage

1. **Upload Documents** (Documents tab):
   - Click "📄 Documents"
   - Drag and drop PDF or click to select
   - Enter document title
   - Wait for "Ready" status

2. **Ask Questions** (Chat tab):
   - Click "💬 Chat"
   - Type your question
   - View answer with source citations

## Project Structure

```
helpai/
├── backend/
│   ├── src/
│   │   ├── api/           # FastAPI routes and main app
│   │   ├── models/        # Pydantic data models
│   │   ├── services/      # Business logic
│   │   │   ├── document/  # PDF processing
│   │   │   ├── llm/       # Ollama integration
│   │   │   ├── query/     # RAG pipeline
│   │   │   ├── session/   # Session management
│   │   │   └── vectordb/  # ChromaDB wrapper
│   │   └── config/        # Settings
│   ├── tests/
│   ├── data/              # Uploads and ChromaDB (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API client
│   │   ├── types/         # TypeScript types
│   │   └── App.tsx        # Main app
│   ├── package.json
│   └── vite.config.ts
├── specs/                 # Feature specifications
├── STARTUP_GUIDE.md      # Detailed setup guide
└── README.md             # This file
```

## Configuration

### Backend (.env)
- `OLLAMA_BASE_URL`: Ollama API URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Model to use (default: llama3.2:3b)
- `CHROMA_PERSIST_DIR`: ChromaDB storage location
- `UPLOAD_DIR`: PDF upload directory
- `MAX_FILE_SIZE_MB`: Max file size (default: 50MB)
- `SESSION_TIMEOUT_MINUTES`: Session timeout (default: 30)

### Frontend (.env)
- `VITE_API_BASE_URL`: Backend API URL (default: http://localhost:8000)

## API Endpoints

- `GET /health` - Health check
- `POST /api/query` - Submit question
- `GET /api/sessions/{id}` - Get session info
- `DELETE /api/sessions/{id}` - Delete session
- `POST /api/documents` - Upload document
- `GET /api/documents` - List documents
- `GET /api/documents/{id}` - Get document
- `DELETE /api/documents/{id}` - Delete document

## Development

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Code Quality
```bash
# Backend
cd backend
ruff check .

# Frontend
cd frontend
npm run lint
```

## Troubleshooting

See [STARTUP_GUIDE.md](STARTUP_GUIDE.md) for detailed troubleshooting steps.

Common issues:
- **Ollama not responding**: Run `ollama serve`
- **Model not found**: Run `ollama pull llama3.2:3b`
- **Import errors**: Reinstall dependencies with `pip install -r requirements.txt`
- **Port conflicts**: Check if ports 8000 (backend) and 5173 (frontend) are available

## Performance

- **Query response**: 3-10 seconds (depends on model and question complexity)
- **Document processing**: 30 seconds - 2 minutes per 100 pages
- **Concurrent users**: 1-5 users (in-memory sessions)
- **Model options**:
  - `llama3.2:3b` - Fast, lightweight
  - `llama3.1:8b` - Better quality
  - `mistral:7b` - Good balance

## Privacy & Security

- All processing happens locally (no external API calls)
- No query/response logging
- In-memory sessions (cleared on restart)
- Uploaded documents stored locally in `data/uploads/`
- Basic security (suitable for personal/small team use)

