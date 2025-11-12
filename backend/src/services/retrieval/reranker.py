"""Reranking service for improving retrieval quality."""

import logging
from typing import List, Optional
from flashrank import Ranker, RerankRequest

from ...models.chunk import SearchResult

logger = logging.getLogger(__name__)


class Reranker:
    """
    Reranking service using FlashRank.
    """

    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2"):
        self.model_name = model_name
        self.ranker: Optional[Ranker] = None
        self._initialize_ranker()

    def _initialize_ranker(self) -> None:
        """Initialize the FlashRank model."""
        try:
            logger.info(f"Initializing FlashRank reranker with model: {self.model_name}")
            self.ranker = Ranker(model_name=self.model_name)
            logger.info("FlashRank reranker initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize reranker: {e}")
            self.ranker = None

    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Rerank search results based on relevance to the query.

        """
        if not results:
            logger.debug("No results to rerank")
            return []

        if not self.ranker:
            logger.warning("Reranker not initialized, returning original results")
            return results[:top_k] if top_k else results

        try:
            # Prepare reranking request
            passages = [
                {"text": result.content, "meta": {"chunk_id": result.chunk_id}}
                for result in results
            ]

            rerank_request = RerankRequest(
                query=query,
                passages=passages
            )

            # Perform reranking
            reranked = self.ranker.rerank(rerank_request)

            # Map reranked results back to SearchResult objects
            reranked_results = []
            for item in reranked:
                # Find original result by chunk_id
                chunk_id = item["meta"]["chunk_id"]
                original_result = next(
                    (r for r in results if r.chunk_id == chunk_id),
                    None
                )

                if original_result:
                    # Create new SearchResult with reranking score
                    # Note: metadata values must be strings as per SearchResult model
                    reranked_result = SearchResult(
                        chunk_id=original_result.chunk_id,
                        document_id=original_result.document_id,
                        content=original_result.content,
                        similarity_score=float(item["score"]),  # Update with rerank score
                        page_number=original_result.page_number,
                        metadata={
                            **(original_result.metadata or {}),
                            "original_score": str(original_result.similarity_score),
                            "rerank_score": str(float(item["score"]))
                        }
                    )
                    reranked_results.append(reranked_result)

            # Apply top_k if specified
            if top_k:
                reranked_results = reranked_results[:top_k]

            logger.info(f"Reranked {len(results)} results to {len(reranked_results)} results")
            return reranked_results

        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Fallback to original results
            return results[:top_k] if top_k else results

    def is_available(self) -> bool:
        """
        Check if the reranker is available and ready to use.

        """
        return self.ranker is not None
