"""FastAPI application for Legal Document Assistant."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import settings
from ..services.document.storage import DocumentStorage
from ..services.session.manager import SessionManager
from ..services.vectordb.client import ChromaDBClient
from . import dependencies

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting Legal Document Assistant API")

    try:
        # Initialize ChromaDB
        logger.info("Initializing ChromaDB with hybrid search and reranking...")
        dependencies.chromadb_client = ChromaDBClient(
            persist_directory=settings.chroma_persist_dir,
            enable_hybrid_search=settings.enable_hybrid_search,
            enable_reranking=settings.enable_reranking,
            reranker_model=settings.reranker_model,
            rrf_k=settings.rrf_k,
            dense_weight=settings.dense_weight,
            sparse_weight=settings.sparse_weight,
        )
        dependencies.chromadb_client.initialize()

        # Initialize Session Manager
        logger.info("Initializing Session Manager...")
        dependencies.session_manager = SessionManager(
            timeout_minutes=settings.session_timeout_minutes
        )
        await dependencies.session_manager.start_cleanup_task()

        # Initialize Document Storage
        logger.info("Initializing Document Storage...")
        dependencies.document_storage = DocumentStorage(upload_dir=settings.upload_dir)

        logger.info("Application startup complete")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Legal Document Assistant API")

    try:
        # Stop session cleanup task
        if dependencies.session_manager:
            await dependencies.session_manager.stop_cleanup_task()

        # Shutdown ChromaDB
        if dependencies.chromadb_client:
            dependencies.chromadb_client.shutdown()

        logger.info("Application shutdown complete")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Legal Document Assistant API",
    description="Text-based legal document Q&A system using RAG",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:3000",  # Alternative dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers (must be after app creation to avoid circular imports)
from .routes import documents, health, query, sessions  # noqa: E402

app.include_router(health.router, tags=["health"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
