"""Query endpoint for Q&A functionality."""

import json
import logging
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ...config.settings import settings
from ...models.query import UserQuery, QueryResponse
from ...services.llm.ollama_client import OllamaClient
from ...services.query.processor import QueryProcessor
from ...services.session.manager import SessionManager
from ...services.vectordb.client import ChromaDBClient
from ..dependencies import get_chromadb_client, get_session_manager

logger = logging.getLogger(__name__)

router = APIRouter()


def get_query_processor(
    chromadb_client: ChromaDBClient = Depends(get_chromadb_client),
) -> QueryProcessor:
    """
    Dependency to get query processor.

    Args:
        chromadb_client: ChromaDB client instance

    Returns:
        QueryProcessor instance
    """
    # Initialize LLM client
    llm_client = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model
    )

    # Create and return query processor with hybrid search settings
    return QueryProcessor(
        vectordb_client=chromadb_client,
        llm_client=llm_client,
        num_results=settings.num_retrieval_results,
        use_hybrid_search=settings.enable_hybrid_search,
        use_reranking=settings.enable_reranking
    )


@router.post("/query", response_model=QueryResponse)
async def submit_query(
    request: UserQuery,
    query_processor: QueryProcessor = Depends(get_query_processor),
    session_manager: SessionManager = Depends(get_session_manager)
) -> QueryResponse:
    """
    Submit a query and get a response.

    Args:
        request: User query request
        query_processor: Query processor instance
        session_manager: Session manager instance

    Returns:
        Query response with generated answer and source documents

    Raises:
        HTTPException: If query processing fails
    """
    try:
        # Get or create session
        session = session_manager.get_or_create_session(request.session_id)

        # Add user message to session
        session.add_message(role="user", content=request.query_text)

        logger.info(
            f"Processing query for session {session.session_id}: '{request.query_text[:50]}...'"
        )

        # Process the query
        response_text, search_results, processing_time_ms = await query_processor.process_query(
            query_text=request.query_text,
            session=session
        )

        # Add assistant response to session
        session.add_message(role="assistant", content=response_text)

        # Format response
        query_response = query_processor.format_query_response(
            response_text=response_text,
            search_results=search_results,
            session_id=session.session_id,
            processing_time_ms=processing_time_ms
        )

        logger.info(
            f"Query completed. Processing time: {processing_time_ms:.2f}ms, "
            f"Sources: {len(search_results)}"
        )

        return query_response

    except Exception as e:
        logger.error(f"Failed to process query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/query/stream")
async def submit_query_stream(
    request: UserQuery,
    query_processor: QueryProcessor = Depends(get_query_processor),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Submit a query and get a streaming response.

    Args:
        request: User query request
        query_processor: Query processor instance
        session_manager: Session manager instance

    Returns:
        StreamingResponse with Server-Sent Events

    Raises:
        HTTPException: If query processing fails
    """
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            start_time = time.time()

            # Get or create session
            session = session_manager.get_or_create_session(request.session_id)

            # Add user message to session
            session.add_message(role="user", content=request.query_text)

            logger.info(
                f"Processing streaming query for session {session.session_id}: '{request.query_text[:50]}...'"
            )

            # Step 1: Retrieve relevant documents using hybrid search
            if query_processor.use_hybrid_search and query_processor.vectordb_client.enable_hybrid_search:
                search_results = query_processor.vectordb_client.search_hybrid(
                    query=request.query_text,
                    top_k=query_processor.num_results,
                    apply_reranking=query_processor.use_reranking,
                    dense_top_k=settings.dense_retrieval_top_k,
                    sparse_top_k=settings.sparse_retrieval_top_k
                )
            else:
                search_results = query_processor.vectordb_client.search_similar(
                    query=request.query_text,
                    n_results=query_processor.num_results
                )

            # Send sources first
            sources_data = {
                "type": "sources",
                "sources": [
                    {
                        "document_id": str(result.document_id),
                        "chunk_id": result.chunk_id,
                        "content": result.content,
                        "page_number": result.page_number,
                        "similarity_score": result.similarity_score
                    }
                    for result in search_results
                ],
                "session_id": str(session.session_id)
            }
            yield f"data: {json.dumps(sources_data)}\n\n"

            # Build prompt
            if session and len(session.messages) > 0:
                from ...services.llm.prompts import build_contextual_prompt
                context_messages = session.get_context_messages(max_messages=4)
                prompt = build_contextual_prompt(
                    query=request.query_text,
                    search_results=search_results,
                    conversation_context=context_messages
                )
            else:
                from ...services.llm.prompts import build_rag_prompt
                prompt = build_rag_prompt(
                    query=request.query_text,
                    search_results=search_results
                )

            # Stream the response
            full_response = ""
            async for chunk in query_processor.llm_client.generate_response_stream(
                prompt=prompt,
                temperature=0.7
            ):
                full_response += chunk
                chunk_data = {
                    "type": "token",
                    "content": chunk
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"

            # Add assistant response to session
            session.add_message(role="assistant", content=full_response)

            # Send completion
            processing_time_ms = (time.time() - start_time) * 1000
            completion_data = {
                "type": "done",
                "session_id": str(session.session_id),
                "processing_time_ms": processing_time_ms
            }
            yield f"data: {json.dumps(completion_data)}\n\n"

            logger.info(
                f"Streaming query completed. Processing time: {processing_time_ms:.2f}ms"
            )

        except Exception as e:
            logger.error(f"Failed to process streaming query: {e}")
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
