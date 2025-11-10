"""Query processing service for RAG pipeline."""

import logging
import time
from typing import List, Optional
from uuid import UUID

from ...models.chunk import SearchResult
from ...models.query import QueryResponse, SourceDocument
from ...models.session import ConversationSession
from ..llm.ollama_client import OllamaClient
from ..llm.prompts import build_rag_prompt, build_contextual_prompt
from ..vectordb.client import ChromaDBClient

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Processes user queries using RAG (Retrieval-Augmented Generation)."""

    def __init__(
        self,
        vectordb_client: ChromaDBClient,
        llm_client: OllamaClient,
        num_results: int = 5
    ):
        """
        Initialize query processor.

        Args:
            vectordb_client: ChromaDB client for vector search
            llm_client: Ollama client for text generation
            num_results: Number of documents to retrieve
        """
        self.vectordb_client = vectordb_client
        self.llm_client = llm_client
        self.num_results = num_results

    async def process_query(
        self,
        query_text: str,
        session: Optional[ConversationSession] = None
    ) -> tuple[str, List[SearchResult], float]:
        """
        Process a user query using RAG pipeline.

        Args:
            query_text: User's question
            session: Optional conversation session for context

        Returns:
            Tuple of (response_text, source_results, processing_time_ms)

        Raises:
            Exception: If query processing fails
        """
        start_time = time.time()

        try:
            # Step 1: Retrieve relevant documents
            logger.info(f"Searching for relevant documents: '{query_text[:50]}...'")
            search_results = self.vectordb_client.search_similar(
                query=query_text,
                n_results=self.num_results
            )

            if not search_results:
                logger.warning("No relevant documents found")
                return (
                    "I don't have any documents to reference. Please upload legal documents first.",
                    [],
                    (time.time() - start_time) * 1000
                )

            # Step 2: Build prompt
            if session and len(session.messages) > 0:
                # Use contextual prompt with conversation history
                context_messages = session.get_context_messages(max_messages=4)
                prompt = build_contextual_prompt(
                    query=query_text,
                    search_results=search_results,
                    conversation_context=context_messages
                )
            else:
                # Use simple RAG prompt
                prompt = build_rag_prompt(
                    query=query_text,
                    search_results=search_results
                )

            # Step 3: Generate response using LLM
            logger.info("Generating response with LLM")
            response_text = await self.llm_client.generate_response(
                prompt=prompt,
                context_messages=None,  # Context already in prompt
                temperature=0.7
            )

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Query processed successfully in {processing_time_ms:.2f}ms. "
                f"Retrieved {len(search_results)} documents."
            )

            return response_text, search_results, processing_time_ms

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Failed to process query: {e}")
            raise

    def format_query_response(
        self,
        response_text: str,
        search_results: List[SearchResult],
        session_id: UUID,
        processing_time_ms: float
    ) -> QueryResponse:
        """
        Format the query response for API output.

        Args:
            response_text: Generated response text
            search_results: Retrieved document chunks
            session_id: Session identifier
            processing_time_ms: Processing time in milliseconds

        Returns:
            QueryResponse object
        """
        # Convert search results to source documents
        source_documents = [
            SourceDocument(
                document_id=result.document_id,
                chunk_id=result.chunk_id,
                content=result.content,
                page_number=result.page_number,
                similarity_score=result.similarity_score
            )
            for result in search_results
        ]

        return QueryResponse(
            response_text=response_text,
            source_documents=source_documents,
            session_id=session_id,
            processing_time_ms=processing_time_ms
        )
