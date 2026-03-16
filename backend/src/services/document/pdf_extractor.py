"""PDF text extraction service using PyMuPDF."""

import logging
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extracts text from PDF documents."""

    @staticmethod
    def extract_text_from_pdf(file_path: Path) -> list[tuple[int, str]]:
        """
        Extract text from a PDF file.


        """
        try:
            logger.info(f"Extracting text from PDF: {file_path}")

            # Open the PDF
            doc = fitz.open(file_path)

            pages_text = []

            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                # Only include pages with content
                if text.strip():
                    pages_text.append((page_num + 1, text))  # 1-indexed page numbers

            doc.close()

            logger.info(
                f"Extracted text from {len(pages_text)} pages "
                f"(total {sum(len(text) for _, text in pages_text)} characters)"
            )

            return pages_text

        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            raise

    @staticmethod
    def get_pdf_metadata(file_path: Path) -> dict:
        """
        Extract metadata from a PDF file.

        """
        try:
            doc = fitz.open(file_path)

            metadata = {
                "page_count": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
            }

            doc.close()

            return metadata

        except Exception as e:
            logger.error(f"Failed to extract metadata from PDF {file_path}: {e}")
            raise

    @staticmethod
    def validate_pdf(file_path: Path) -> bool:
        """
        Validate that a file is a readable PDF.

        """
        try:
            doc = fitz.open(file_path)
            is_valid = len(doc) > 0
            doc.close()
            return is_valid

        except Exception as e:
            logger.warning(f"PDF validation failed for {file_path}: {e}")
            return False
