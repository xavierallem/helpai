"""BM25 sparse retrieval service for keyword-based document search."""

import logging
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
import re
from collections import defaultdict

from ...models.chunk import DocumentChunk, SearchResult

logger = logging.getLogger(__name__)


class BM25Retriever:
    """
    BM25-based sparse retrieval for keyword matching.
    """

    def __init__(self):
        """Initialize the BM25 retriever."""
        self.bm25: Optional[BM25Okapi] = None
        self.chunks: List[DocumentChunk] = []
        self.chunk_id_to_idx: Dict[str, int] = {}
        self.document_chunks: Dict[str, List[int]] = defaultdict(list)
        logger.info("BM25Retriever initialized")

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization: lowercase and split on non-alphanumeric characters.

        """
        # Convert to lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\w+', text.lower())
        return tokens

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Add document chunks to the BM25 index.

        Args:
            chunks: List of document chunks to index
        """
        if not chunks:
            logger.warning("No chunks provided to add to BM25 index")
            return

        for chunk in chunks:
            # Add chunk to list
            idx = len(self.chunks)
            self.chunks.append(chunk)
            self.chunk_id_to_idx[chunk.chunk_id] = idx
            self.document_chunks[chunk.document_id].append(idx)

        # Rebuild BM25 index with all chunks
        self._rebuild_index()

        logger.info(f"Added {len(chunks)} chunks to BM25 index. Total chunks: {len(self.chunks)}")

    def _rebuild_index(self) -> None:
        """Rebuild the BM25 index from all stored chunks."""
        if not self.chunks:
            self.bm25 = None
            return

        # Tokenize all chunk contents
        tokenized_corpus = [self._tokenize(chunk.content) for chunk in self.chunks]

        # Create BM25 index
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.debug(f"BM25 index rebuilt with {len(self.chunks)} chunks")

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Search for relevant chunks using BM25.
        """
        if not self.bm25 or not self.chunks:
            logger.warning("BM25 index is empty, returning no results")
            return []

        # Tokenize query
        tokenized_query = self._tokenize(query)

        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        # Get max score for normalization
        max_score = max(scores[idx] for idx in top_indices if scores[idx] > 0) if top_indices and scores[top_indices[0]] > 0 else 1.0

        # Convert to SearchResult objects
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include documents with positive scores
                chunk = self.chunks[idx]
                # Normalize BM25 score to 0-1 range
                normalized_score = min(1.0, scores[idx] / max_score) if max_score > 0 else 0.0
                results.append(SearchResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    similarity_score=float(normalized_score),
                    page_number=chunk.page_number,
                    metadata=chunk.metadata
                ))

        logger.info(f"BM25 search for '{query[:50]}...' returned {len(results)} results")
        return results

    def delete_document_chunks(self, document_id: str) -> int:
        """
        Remove all chunks for a specific document from the index.

        """
        if document_id not in self.document_chunks:
            logger.warning(f"Document {document_id} not found in BM25 index")
            return 0

        # Get indices to remove
        indices_to_remove = set(self.document_chunks[document_id])

        # Remove chunks and update mappings
        new_chunks = []
        new_chunk_id_to_idx = {}
        new_document_chunks = defaultdict(list)

        for idx, chunk in enumerate(self.chunks):
            if idx not in indices_to_remove:
                new_idx = len(new_chunks)
                new_chunks.append(chunk)
                new_chunk_id_to_idx[chunk.chunk_id] = new_idx
                new_document_chunks[chunk.document_id].append(new_idx)

        chunks_removed = len(self.chunks) - len(new_chunks)

        # Update internal state
        self.chunks = new_chunks
        self.chunk_id_to_idx = new_chunk_id_to_idx
        self.document_chunks = new_document_chunks

        # Rebuild index
        self._rebuild_index()

        logger.info(f"Removed {chunks_removed} chunks for document {document_id} from BM25 index")
        return chunks_removed

    def get_stats(self) -> Dict:
        """
        Get statistics about the BM25 index.
        """
        return {
            "total_chunks": len(self.chunks),
            "total_documents": len(self.document_chunks),
            "index_ready": self.bm25 is not None
        }

    def clear(self) -> None:
        """Clear all data from the BM25 index."""
        self.bm25 = None
        self.chunks = []
        self.chunk_id_to_idx = {}
        self.document_chunks = defaultdict(list)
        logger.info("BM25 index cleared")
