"""Unit tests for Pydantic models."""

from uuid import uuid4

from pydantic import ValidationError
import pytest

from src.models.document import LegalDocument, ProcessingStatus
from src.models.query import QueryResponse, SourceDocument, UserQuery
from src.models.session import ConversationSession, Message


# ---------------------------------------------------------------------------
# LegalDocument
# ---------------------------------------------------------------------------

class TestLegalDocument:
    def test_defaults(self):
        doc = LegalDocument(title="Contract", file_path="/tmp/contract.pdf")
        assert doc.processing_status == ProcessingStatus.PENDING
        assert doc.total_chunks == 0
        assert doc.file_size_bytes == 0
        assert doc.processed_at is None
        assert doc.error_message is None
        assert doc.document_id is not None

    def test_title_required(self):
        with pytest.raises(ValidationError):
            LegalDocument(file_path="/tmp/x.pdf")

    def test_title_too_long(self):
        with pytest.raises(ValidationError):
            LegalDocument(title="x" * 501, file_path="/tmp/x.pdf")

    def test_title_empty(self):
        with pytest.raises(ValidationError):
            LegalDocument(title="", file_path="/tmp/x.pdf")

    def test_processing_status_values(self):
        for status in ProcessingStatus:
            doc = LegalDocument(
                title="Doc",
                file_path="/tmp/x.pdf",
                processing_status=status,
            )
            assert doc.processing_status == status


# ---------------------------------------------------------------------------
# ConversationSession & Message
# ---------------------------------------------------------------------------

class TestConversationSession:
    def test_create_empty_session(self):
        session = ConversationSession()
        assert session.messages == []
        assert session.session_id is not None

    def test_add_messages(self):
        session = ConversationSession()
        session.add_message(role="user", content="Hello")
        session.add_message(role="assistant", content="Hi there")
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"

    def test_add_message_updates_last_activity(self):
        session = ConversationSession()
        before = session.last_activity
        session.add_message(role="user", content="Ping")
        assert session.last_activity >= before

    def test_get_context_messages(self):
        session = ConversationSession()
        for i in range(15):
            session.add_message(role="user", content=f"msg {i}")
        ctx = session.get_context_messages(max_messages=10)
        assert len(ctx) == 10
        assert ctx[-1]["content"] == "msg 14"

    def test_invalid_role_raises(self):
        with pytest.raises(ValidationError):
            Message(role="system", content="Not allowed")

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError):
            Message(role="user", content="")


# ---------------------------------------------------------------------------
# UserQuery
# ---------------------------------------------------------------------------

class TestUserQuery:
    def test_valid_query(self):
        q = UserQuery(query_text="What is the indemnification clause?")
        assert q.session_id is None

    def test_with_session_id(self):
        sid = uuid4()
        q = UserQuery(query_text="Explain damages", session_id=sid)
        assert q.session_id == sid

    def test_empty_query_raises(self):
        with pytest.raises(ValidationError):
            UserQuery(query_text="")

    def test_too_long_query_raises(self):
        with pytest.raises(ValidationError):
            UserQuery(query_text="x" * 2001)


# ---------------------------------------------------------------------------
# SourceDocument & QueryResponse
# ---------------------------------------------------------------------------

class TestSourceDocument:
    def test_valid(self):
        sd = SourceDocument(
            document_id=uuid4(),
            chunk_id="chunk-1",
            content="Some text",
            similarity_score=0.85,
        )
        assert sd.page_number is None

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            SourceDocument(
                document_id=uuid4(),
                chunk_id="c",
                content="text",
                similarity_score=1.5,
            )


class TestQueryResponse:
    def test_valid(self):
        qr = QueryResponse(
            response_text="The clause states...",
            source_documents=[],
            session_id=uuid4(),
            processing_time_ms=120.5,
        )
        assert qr.response_text == "The clause states..."
