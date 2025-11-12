"""Hybrid retrieval combining dense and sparse search with reranking."""

import logging
from typing import List, Dict, Optional
from collections import defaultdict

from ...models.chunk import SearchResult
from .bm25_retriever import BM25Retriever
from .reranker import Reranker

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid retrieval system combining dense and sparse search.


    """

    def __init__(
        self,
        bm25_retriever: BM25Retriever,
        reranker: Optional[Reranker] = None,
        rrf_k: int = 60,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5
    ):

        self.bm25_retriever = bm25_retriever
        self.reranker = reranker
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight

        logger.info(
            f"HybridRetriever initialized with RRF_K={rrf_k}, "
            f"dense_weight={dense_weight}, sparse_weight={sparse_weight}"
        )

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Merge results using Reciprocal Rank Fusion (RRF).
        """
        # Create a mapping of chunk_id to SearchResult
        chunk_map: Dict[str, SearchResult] = {}
        rrf_scores: Dict[str, float] = defaultdict(float)

        # Process dense results
        for rank, result in enumerate(dense_results, start=1):
            chunk_id = result.chunk_id
            chunk_map[chunk_id] = result
            rrf_score = self.dense_weight / (self.rrf_k + rank)
            rrf_scores[chunk_id] += rrf_score

        # Process sparse results
        for rank, result in enumerate(sparse_results, start=1):
            chunk_id = result.chunk_id
            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = result
            rrf_score = self.sparse_weight / (self.rrf_k + rank)
            rrf_scores[chunk_id] += rrf_score

        # Sort by RRF score
        sorted_chunk_ids = sorted(
            rrf_scores.keys(),
            key=lambda cid: rrf_scores[cid],
            reverse=True
        )

        # Create merged results with RRF scores
        merged_results = []
        for chunk_id in sorted_chunk_ids:
            result = chunk_map[chunk_id]
            # Create new result with RRF score
            # Note: metadata values must be strings as per SearchResult model
            merged_result = SearchResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                content=result.content,
                similarity_score=rrf_scores[chunk_id],  # RRF score
                page_number=result.page_number,
                metadata={
                    **(result.metadata or {}),
                    "rrf_score": str(rrf_scores[chunk_id]),
                    "original_score": str(result.similarity_score)
                }
            )
            merged_results.append(merged_result)

        logger.debug(
            f"RRF merged {len(dense_results)} dense + {len(sparse_results)} sparse "
            f"results into {len(merged_results)} unique results"
        )

        return merged_results

    def retrieve(
        self,
        query: str,
        dense_results: List[SearchResult],
        top_k: int = 5,
        apply_reranking: bool = True,
        dense_top_k: int = 20,
        sparse_top_k: int = 20
    ) -> List[SearchResult]:
        """
        Perform hybrid retrieval combining dense and sparse search.

        """
        # Limit dense results to top_k for fusion
        dense_results = dense_results[:dense_top_k]

        # Get sparse results from BM25
        sparse_results = self.bm25_retriever.search(query, top_k=sparse_top_k)

        logger.info(
            f"Hybrid retrieval: {len(dense_results)} dense + "
            f"{len(sparse_results)} sparse results"
        )

        # Merge using RRF
        merged_results = self._reciprocal_rank_fusion(dense_results, sparse_results)

        # Apply reranking if enabled and available
        if apply_reranking and self.reranker and self.reranker.is_available():
            logger.info("Applying reranking to hybrid results")
            # Take more results for reranking (e.g., 2x top_k) then rerank to top_k
            rerank_candidates = merged_results[:top_k * 2]
            final_results = self.reranker.rerank(
                query=query,
                results=rerank_candidates,
                top_k=top_k
            )
        else:
            # No reranking, just return top_k results
            final_results = merged_results[:top_k]

        logger.info(f"Hybrid retrieval returned {len(final_results)} final results")
        return final_results

    def get_stats(self) -> Dict:
        """
        Get statistics about the hybrid retriever.

        """
        return {
            "bm25_stats": self.bm25_retriever.get_stats(),
            "reranker_available": self.reranker.is_available() if self.reranker else False,
            "rrf_k": self.rrf_k,
            "dense_weight": self.dense_weight,
            "sparse_weight": self.sparse_weight
        }
