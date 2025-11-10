"""Document chunk models for vector database storage."""

from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Document chunk model for vector database storage."""

    chunk_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the chunk"
    )
    document_id: UUID = Field(
        ...,
        description="ID of the parent document"
    )
    content: str = Field(
        ...,
        description="Text content of the chunk",
        min_length=1
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Page number where this chunk appears"
    )
    chunk_index: int = Field(
        ...,
        description="Sequential index of this chunk within the document"
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional metadata for the chunk"
    )

    def to_chromadb_format(self) -> tuple[str, str, Dict]:
        """
        Convert chunk to ChromaDB storage format.

        Returns:
            Tuple of (chunk_id, content, metadata)
        """
        chromadb_metadata = {
            "document_id": str(self.document_id),
            "chunk_index": str(self.chunk_index),
            **self.metadata
        }

        if self.page_number is not None:
            chromadb_metadata["page_number"] = str(self.page_number)

        return self.chunk_id, self.content, chromadb_metadata


class SearchResult(BaseModel):
    """Search result from vector database."""

    chunk_id: str = Field(
        ...,
        description="ID of the matching chunk"
    )
    document_id: UUID = Field(
        ...,
        description="ID of the source document"
    )
    content: str = Field(
        ...,
        description="Text content of the matching chunk"
    )
    similarity_score: float = Field(
        ...,
        description="Similarity score (0-1, higher is more similar)",
        ge=0.0,
        le=1.0
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Page number of the chunk"
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    @classmethod
    def from_chromadb_result(
        cls,
        chunk_id: str,
        content: str,
        metadata: Dict,
        distance: float
    ) -> "SearchResult":
        """
        Create SearchResult from ChromaDB query result.

        Args:
            chunk_id: Chunk identifier
            content: Chunk text content
            metadata: Chunk metadata from ChromaDB
            distance: Distance score (lower is more similar)

        Returns:
            SearchResult instance
        """
        # Convert distance to similarity (ChromaDB uses L2 distance)
        # For normalized embeddings, similarity = 1 - (distance^2 / 4)
        similarity_score = max(0.0, min(1.0, 1.0 - (distance / 2.0)))

        page_number = None
        if "page_number" in metadata:
            try:
                page_number = int(metadata["page_number"])
            except (ValueError, TypeError):
                pass

        return cls(
            chunk_id=chunk_id,
            document_id=UUID(metadata["document_id"]),
            content=content,
            similarity_score=similarity_score,
            page_number=page_number,
            metadata=metadata
        )
