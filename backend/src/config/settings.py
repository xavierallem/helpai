"""Application configuration settings."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama API"
    )
    ollama_model: str = Field(
        default="llama3.2:3b",
        description="Ollama model to use for text generation"
    )

    # ChromaDB Configuration
    chroma_persist_dir: Path = Field(
        default=Path("./data/chromadb"),
        description="Directory to persist ChromaDB data"
    )

    # Hybrid Retrieval Configuration
    enable_hybrid_search: bool = Field(
        default=True,
        description="Enable hybrid search (dense + sparse retrieval)"
    )
    enable_reranking: bool = Field(
        default=True,
        description="Enable reranking of search results"
    )
    reranker_model: str = Field(
        default="ms-marco-MiniLM-L-12-v2",
        description="Reranking model to use (ms-marco-MiniLM-L-12-v2, ms-marco-MultiBERT-L-12, rank-T5-flan)"
    )

    # Retrieval Parameters
    num_retrieval_results: int = Field(
        default=5,
        description="Number of final results to return"
    )
    dense_retrieval_top_k: int = Field(
        default=20,
        description="Number of dense (vector) results to retrieve for fusion"
    )
    sparse_retrieval_top_k: int = Field(
        default=20,
        description="Number of sparse (BM25) results to retrieve for fusion"
    )

    # RRF (Reciprocal Rank Fusion) Parameters
    rrf_k: int = Field(
        default=60,
        description="RRF constant parameter (typically 60)"
    )
    dense_weight: float = Field(
        default=0.5,
        description="Weight for dense retrieval in RRF (0-1)"
    )
    sparse_weight: float = Field(
        default=0.5,
        description="Weight for sparse retrieval in RRF (0-1)"
    )

    # File Upload Configuration
    upload_dir: Path = Field(
        default=Path("./data/uploads"),
        description="Directory to store uploaded files"
    )
    max_file_size_mb: int = Field(
        default=50,
        description="Maximum file size in megabytes"
    )

    # Session Configuration
    session_timeout_minutes: int = Field(
        default=30,
        description="Session timeout in minutes"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API host to bind to"
    )
    api_port: int = Field(
        default=8000,
        description="API port to bind to"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()
