"""ChromaDB client wrapper for vector database operations."""

import logging
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from ...models.chunk import DocumentChunk, SearchResult

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """Wrapper for ChromaDB operations with sentence-transformers embeddings."""

    COLLECTION_NAME = "legal_documents"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, persist_directory: Path):
        """
        Initialize ChromaDB client.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        self.client: Optional[chromadb.ClientAPI] = None
        self.collection: Optional[chromadb.Collection] = None
        self.embedding_model: Optional[SentenceTransformer] = None

    def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            # Ensure persist directory exists
            self.persist_directory.mkdir(parents=True, exist_ok=True)

            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Initialize embedding model
            logger.info(f"Loading embedding model: {self.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Legal documents and their chunks"}
            )

            logger.info(
                f"ChromaDB initialized. Collection '{self.COLLECTION_NAME}' "
                f"contains {self.collection.count()} chunks"
            )

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Add document chunks to the vector database.

        Args:
            chunks: List of document chunks to add

        Raises:
            RuntimeError: If client is not initialized
        """
        if not self.collection or not self.embedding_model:
            raise RuntimeError("ChromaDB client not initialized. Call initialize() first.")

        if not chunks:
            return

        try:
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []

            for chunk in chunks:
                chunk_id, content, metadata = chunk.to_chromadb_format()
                ids.append(chunk_id)
                documents.append(content)
                metadatas.append(metadata)

            # Generate embeddings
            embeddings = self.embedding_model.encode(
                documents,
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()

            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            logger.info(f"Added {len(chunks)} chunks to ChromaDB")

        except Exception as e:
            logger.error(f"Failed to add chunks to ChromaDB: {e}")
            raise

    def search_similar(
        self,
        query: str,
        n_results: int = 5
    ) -> List[SearchResult]:
        """
        Search for similar chunks using semantic search.

        Args:
            query: Search query text
            n_results: Number of results to return

        Returns:
            List of search results ordered by similarity

        Raises:
            RuntimeError: If client is not initialized
        """
        if not self.collection or not self.embedding_model:
            raise RuntimeError("ChromaDB client not initialized. Call initialize() first.")

        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(
                [query],
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()[0]

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )

            # Convert to SearchResult objects
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    search_result = SearchResult.from_chromadb_result(
                        chunk_id=results["ids"][0][i],
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i],
                        distance=results["distances"][0][i]
                    )
                    search_results.append(search_result)

            logger.info(f"Found {len(search_results)} similar chunks for query")
            return search_results

        except Exception as e:
            logger.error(f"Failed to search ChromaDB: {e}")
            raise

    def delete_document_chunks(self, document_id: str) -> None:
        """
        Delete all chunks for a specific document.

        Args:
            document_id: Document ID whose chunks should be deleted

        Raises:
            RuntimeError: If client is not initialized
        """
        if not self.collection:
            raise RuntimeError("ChromaDB client not initialized. Call initialize() first.")

        try:
            self.collection.delete(
                where={"document_id": document_id}
            )
            logger.info(f"Deleted chunks for document {document_id}")

        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {e}")
            raise

    def get_collection_stats(self) -> dict:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection statistics

        Raises:
            RuntimeError: If client is not initialized
        """
        if not self.collection:
            raise RuntimeError("ChromaDB client not initialized. Call initialize() first.")

        try:
            return {
                "total_chunks": self.collection.count(),
                "collection_name": self.COLLECTION_NAME,
                "embedding_model": self.EMBEDDING_MODEL
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise

    def shutdown(self) -> None:
        """Shutdown the ChromaDB client."""
        logger.info("Shutting down ChromaDB client")
        # ChromaDB client doesn't require explicit cleanup
        self.client = None
        self.collection = None
        self.embedding_model = None
