"""Unit tests for TextChunker."""

from uuid import uuid4

import pytest

from src.services.document.text_chunker import TextChunker


class TestTextChunker:
    @pytest.fixture
    def chunker(self):
        return TextChunker(chunk_size=200, chunk_overlap=20)

    def test_chunk_single_page(self, chunker):
        doc_id = uuid4()
        text = "This is a sentence. " * 30  # ~600 chars
        chunks = chunker.chunk_document(doc_id, [(1, text)])
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.document_id == doc_id
            assert chunk.page_number == 1
            assert len(chunk.content) > 0

    def test_chunk_multiple_pages(self, chunker):
        doc_id = uuid4()
        pages = [(i, f"Page {i} content. " * 20) for i in range(1, 4)]
        chunks = chunker.chunk_document(doc_id, pages)
        page_numbers = {c.page_number for c in chunks}
        assert page_numbers == {1, 2, 3}

    def test_empty_page_skipped(self, chunker):
        doc_id = uuid4()
        chunks = chunker.chunk_document(doc_id, [(1, "   "), (2, "Real content here. " * 20)])
        page_numbers = {c.page_number for c in chunks}
        assert 1 not in page_numbers
        assert 2 in page_numbers

    def test_chunk_index_increments(self, chunker):
        doc_id = uuid4()
        text = "Word " * 200
        chunks = chunker.chunk_document(doc_id, [(1, text)])
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(indices)))

    def test_empty_document_returns_no_chunks(self, chunker):
        chunks = chunker.chunk_document(uuid4(), [])
        assert chunks == []

    def test_chunk_metadata(self, chunker):
        doc_id = uuid4()
        chunks = chunker.chunk_document(doc_id, [(3, "Some text content. " * 20)])
        for chunk in chunks:
            assert "page" in chunk.metadata
            assert chunk.metadata["page"] == "3"
            assert "chunk_size" in chunk.metadata

    def test_chunk_size_respected(self, chunker):
        doc_id = uuid4()
        long_text = "A" * 2000
        chunks = chunker.chunk_document(doc_id, [(1, long_text)])
        # Allow some tolerance for the splitter
        for chunk in chunks:
            assert len(chunk.content) <= chunker.chunk_size * 1.2
