"""Text chunking service for splitting documents into smaller pieces."""

import logging
from typing import List, Tuple
from uuid import UUID

from langchain.text_splitter import RecursiveCharacterTextSplitter

from ...models.chunk import DocumentChunk

logger = logging.getLogger(__name__)


class TextChunker:
    """Chunks text into smaller pieces for vector storage."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize LangChain text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_document(
        self,
        document_id: UUID,
        pages_text: List[Tuple[int, str]]
    ) -> List[DocumentChunk]:
        """
        Chunk a document into smaller pieces.


        """
        try:
            logger.info(
                f"Chunking document {document_id} with {len(pages_text)} pages"
            )

            chunks = []
            chunk_index = 0

            for page_number, page_text in pages_text:
                # Skip empty pages
                if not page_text.strip():
                    continue

                # Split page text into chunks
                page_chunks = self.text_splitter.split_text(page_text)

                # Create DocumentChunk objects
                for chunk_text in page_chunks:
                    chunk = DocumentChunk(
                        document_id=document_id,
                        content=chunk_text,
                        page_number=page_number,
                        chunk_index=chunk_index,
                        metadata={
                            "page": str(page_number),
                            "chunk_size": str(len(chunk_text))
                        }
                    )
                    chunks.append(chunk)
                    chunk_index += 1

            logger.info(
                f"Created {len(chunks)} chunks from document {document_id}. "
                f"Avg chunk size: {sum(len(c.content) for c in chunks) // len(chunks) if chunks else 0} chars"
            )

            return chunks

        except Exception as e:
            logger.error(f"Failed to chunk document {document_id}: {e}")
            raise

    def chunk_text(self, text: str) -> List[str]:
        """
        Simple text chunking without document metadata.

        """
        return self.text_splitter.split_text(text)
