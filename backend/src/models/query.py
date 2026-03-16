"""Query and response models for Q&A functionality."""

from uuid import UUID

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    """Source document citation for a response."""

    document_id: UUID = Field(..., description="ID of the source document")
    chunk_id: str = Field(..., description="ID of the specific chunk")
    content: str = Field(..., description="Relevant excerpt from the document")
    page_number: int | None = Field(default=None, description="Page number in the source document")
    similarity_score: float = Field(..., description="Relevance score (0-1)", ge=0.0, le=1.0)


class UserQuery(BaseModel):
    """User query request model."""

    query_text: str = Field(
        ..., description="The user's question or query", min_length=1, max_length=2000
    )
    session_id: UUID | None = Field(
        default=None, description="Optional session ID for conversation context"
    )


class QueryResponse(BaseModel):
    """Response to a user query."""

    response_text: str = Field(..., description="Generated response to the query")
    source_documents: list[SourceDocument] = Field(
        default_factory=list, description="Source documents used to generate the response"
    )
    session_id: UUID = Field(..., description="Session ID for this conversation")
    processing_time_ms: float = Field(
        ..., description="Time taken to process the query in milliseconds", ge=0.0
    )
