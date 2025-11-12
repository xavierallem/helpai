"""Test script for hybrid RAG implementation."""

import logging
from pathlib import Path
from src.services.retrieval import BM25Retriever, Reranker, HybridRetriever
from src.models.chunk import DocumentChunk, SearchResult
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_bm25_retriever():
    """Test BM25 retriever."""
    logger.info("Testing BM25 Retriever...")

    # Create retriever
    bm25 = BM25Retriever()

    # Create sample chunks
    chunks = [
        DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            content="The legal document states that all contracts must be signed by both parties.",
            chunk_index=0,
            page_number=1
        ),
        DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            content="Employment law requires employers to provide a safe working environment.",
            chunk_index=0,
            page_number=1
        ),
        DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            content="The contract termination clause allows either party to terminate with 30 days notice.",
            chunk_index=0,
            page_number=2
        ),
    ]

    # Add chunks
    bm25.add_chunks(chunks)

    # Search
    query = "contract termination"
    results = bm25.search(query, top_k=2)

    logger.info(f"Query: '{query}'")
    logger.info(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        logger.info(f"  {i}. Score: {result.similarity_score:.4f} - {result.content[:60]}...")

    assert len(results) > 0, "BM25 should return results"
    logger.info("✓ BM25 Retriever test passed")


def test_reranker():
    """Test reranker."""
    logger.info("Testing Reranker...")

    # Create reranker
    reranker = Reranker()

    # Create sample results
    results = [
        SearchResult(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            content="The legal document states that all contracts must be signed by both parties.",
            similarity_score=0.5,
            page_number=1
        ),
        SearchResult(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            content="The contract termination clause allows either party to terminate with 30 days notice.",
            similarity_score=0.4,
            page_number=2
        ),
        SearchResult(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            content="Employment law requires employers to provide a safe working environment.",
            similarity_score=0.3,
            page_number=1
        ),
    ]

    # Rerank
    query = "contract termination"
    reranked = reranker.rerank(query, results, top_k=2)

    logger.info(f"Query: '{query}'")
    logger.info(f"Reranked to {len(reranked)} results:")
    for i, result in enumerate(reranked, 1):
        logger.info(f"  {i}. Score: {result.similarity_score:.4f} - {result.content[:60]}...")

    assert len(reranked) <= 2, "Should return at most top_k results"
    logger.info("✓ Reranker test passed")


def test_hybrid_retriever():
    """Test hybrid retriever."""
    logger.info("Testing Hybrid Retriever...")

    # Create components
    bm25 = BM25Retriever()
    reranker = Reranker()
    hybrid = HybridRetriever(bm25, reranker)

    # Create sample chunks
    doc_id = str(uuid4())
    chunks = [
        DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=doc_id,
            content="The legal document states that all contracts must be signed by both parties.",
            chunk_index=0,
            page_number=1
        ),
        DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=doc_id,
            content="Employment law requires employers to provide a safe working environment.",
            chunk_index=1,
            page_number=1
        ),
        DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=doc_id,
            content="The contract termination clause allows either party to terminate with 30 days notice.",
            chunk_index=2,
            page_number=2
        ),
        DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=doc_id,
            content="Intellectual property rights are protected under federal law.",
            chunk_index=3,
            page_number=3
        ),
    ]

    # Add chunks to BM25
    bm25.add_chunks(chunks)

    # Create dense results (simulating vector search)
    dense_results = [
        SearchResult(
            chunk_id=chunks[0].chunk_id,
            document_id=chunks[0].document_id,
            content=chunks[0].content,
            similarity_score=0.85,
            page_number=chunks[0].page_number
        ),
        SearchResult(
            chunk_id=chunks[2].chunk_id,
            document_id=chunks[2].document_id,
            content=chunks[2].content,
            similarity_score=0.75,
            page_number=chunks[2].page_number
        ),
        SearchResult(
            chunk_id=chunks[1].chunk_id,
            document_id=chunks[1].document_id,
            content=chunks[1].content,
            similarity_score=0.65,
            page_number=chunks[1].page_number
        ),
    ]

    # Perform hybrid retrieval
    query = "contract termination"
    hybrid_results = hybrid.retrieve(
        query=query,
        dense_results=dense_results,
        top_k=2,
        apply_reranking=True
    )

    logger.info(f"Query: '{query}'")
    logger.info(f"Hybrid retrieval returned {len(hybrid_results)} results:")
    for i, result in enumerate(hybrid_results, 1):
        logger.info(f"  {i}. Score: {result.similarity_score:.4f} - {result.content[:60]}...")

    assert len(hybrid_results) <= 2, "Should return at most top_k results"
    logger.info("✓ Hybrid Retriever test passed")


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Testing Hybrid RAG Implementation")
    logger.info("=" * 60)

    try:
        test_bm25_retriever()
        logger.info("")

        test_reranker()
        logger.info("")

        test_hybrid_retriever()
        logger.info("")

        logger.info("=" * 60)
        logger.info("All tests passed! ✓")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
