"""ChromaDB client wrapper for vector database operations."""

import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from ...models.chunk import DocumentChunk, SearchResult
from ..retrieval import BM25Retriever, HybridRetriever, Reranker

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """Wrapper for ChromaDB operations with sentence-transformers embeddings."""

    COLLECTION_NAME = "legal_documents"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    def __init__(
        self,
        persist_directory: Path,
        enable_hybrid_search: bool = True,
        enable_reranking: bool = True,
        reranker_model: str = "ms-marco-MiniLM-L-12-v2",
        rrf_k: int = 60,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
    ):
        """
        Initialize ChromaDB client.

        Args:
            persist_directory: Directory to persist ChromaDB data
            enable_hybrid_search: Whether to enable hybrid (dense + sparse) search
            enable_reranking: Whether to enable result reranking
            reranker_model: Reranking model name
            rrf_k: RRF constant parameter
            dense_weight: Weight for dense retrieval in RRF
            sparse_weight: Weight for sparse retrieval in RRF
        """
        self.persist_directory = persist_directory
        self.enable_hybrid_search = enable_hybrid_search
        self.enable_reranking = enable_reranking
        self.reranker_model = reranker_model
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight

        self.client: chromadb.ClientAPI | None = None
        self.collection: chromadb.Collection | None = None
        self.embedding_model: SentenceTransformer | None = None

        # Hybrid search components
        self.bm25_retriever: BM25Retriever | None = None
        self.reranker: Reranker | None = None
        self.hybrid_retriever: HybridRetriever | None = None

    def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            # Ensure persist directory exists
            self.persist_directory.mkdir(parents=True, exist_ok=True)

            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
            )

            # Initialize embedding model
            logger.info(f"Loading embedding model: {self.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Legal documents and their chunks"},
            )

            logger.info(
                f"ChromaDB initialized. Collection '{self.COLLECTION_NAME}' "
                f"contains {self.collection.count()} chunks"
            )

            # Initialize hybrid search components if enabled
            if self.enable_hybrid_search:
                logger.info("Initializing hybrid search components...")

                # Initialize BM25 retriever
                self.bm25_retriever = BM25Retriever()

                # Initialize reranker if enabled
                if self.enable_reranking:
                    self.reranker = Reranker(model_name=self.reranker_model)
                else:
                    self.reranker = None

                # Initialize hybrid retriever
                self.hybrid_retriever = HybridRetriever(
                    bm25_retriever=self.bm25_retriever,
                    reranker=self.reranker,
                    rrf_k=self.rrf_k,
                    dense_weight=self.dense_weight,
                    sparse_weight=self.sparse_weight,
                )

                logger.info("Hybrid search components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
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
                documents, show_progress_bar=False, convert_to_numpy=True
            ).tolist()

            # Add to collection
            self.collection.add(
                ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
            )

            logger.info(f"Added {len(chunks)} chunks to ChromaDB")

            # Also add to BM25 index if hybrid search is enabled
            if self.enable_hybrid_search and self.bm25_retriever:
                self.bm25_retriever.add_chunks(chunks)
                logger.info(f"Added {len(chunks)} chunks to BM25 index")

        except Exception as e:
            logger.error(f"Failed to add chunks to ChromaDB: {e}")
            raise

    def search_similar(self, query: str, n_results: int = 5) -> list[SearchResult]:
        """
        Search for similar chunks using semantic search.

        """
        if not self.collection or not self.embedding_model:
            raise RuntimeError("ChromaDB client not initialized. Call initialize() first.")

        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(
                [query], show_progress_bar=False, convert_to_numpy=True
            ).tolist()[0]

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            # Convert to SearchResult objects
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    search_result = SearchResult.from_chromadb_result(
                        chunk_id=results["ids"][0][i],
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i],
                        distance=results["distances"][0][i],
                    )
                    search_results.append(search_result)

            logger.info(f"Found {len(search_results)} similar chunks for query")
            return search_results

        except Exception as e:
            logger.error(f"Failed to search ChromaDB: {e}")
            raise

    def search_hybrid(
        self,
        query: str,
        top_k: int = 5,
        apply_reranking: bool = True,
        dense_top_k: int = 20,
        sparse_top_k: int = 20,
    ) -> list[SearchResult]:
        """
        Search using hybrid retrieval (dense + sparse) with optional reranking.

        """
        if not self.enable_hybrid_search or not self.hybrid_retriever:
            # Fallback to regular dense search
            logger.warning("Hybrid search not enabled, falling back to dense search")
            return self.search_similar(query, n_results=top_k)

        try:
            # Get dense results from ChromaDB
            dense_results = self.search_similar(query, n_results=dense_top_k)

            # Perform hybrid retrieval
            hybrid_results = self.hybrid_retriever.retrieve(
                query=query,
                dense_results=dense_results,
                top_k=top_k,
                apply_reranking=apply_reranking and self.enable_reranking,
                dense_top_k=dense_top_k,
                sparse_top_k=sparse_top_k,
            )

            logger.info(f"Hybrid search returned {len(hybrid_results)} results")
            return hybrid_results

        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {e}")
            # Fallback to regular search
            logger.warning("Falling back to dense search due to error")
            return self.search_similar(query, n_results=top_k)

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
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted chunks for document {document_id} from ChromaDB")

            # Also delete from BM25 index if hybrid search is enabled
            if self.enable_hybrid_search and self.bm25_retriever:
                self.bm25_retriever.delete_document_chunks(document_id)
                logger.info(f"Deleted chunks for document {document_id} from BM25 index")

        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {e}")
            raise

    def get_collection_stats(self) -> dict:
        """
        Get statistics about the collection.

        """
        if not self.collection:
            raise RuntimeError("ChromaDB client not initialized. Call initialize() first.")

        try:
            stats = {
                "total_chunks": self.collection.count(),
                "collection_name": self.COLLECTION_NAME,
                "embedding_model": self.EMBEDDING_MODEL,
                "hybrid_search_enabled": self.enable_hybrid_search,
                "reranking_enabled": self.enable_reranking,
            }

            # Add hybrid search stats if enabled
            if self.enable_hybrid_search and self.hybrid_retriever:
                stats["hybrid_retrieval"] = self.hybrid_retriever.get_stats()

            return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise

    def shutdown(self) -> None:
        """Shutdown the ChromaDB client."""
        logger.info("Shutting down ChromaDB client")

        # Clean up hybrid search components
        if self.bm25_retriever:
            self.bm25_retriever.clear()
            self.bm25_retriever = None

        self.reranker = None
        self.hybrid_retriever = None

        # ChromaDB client doesn't require explicit cleanup
        self.client = None
        self.collection = None
        self.embedding_model = None
