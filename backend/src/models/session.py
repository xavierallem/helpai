"""Conversation session models."""

from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Individual message in a conversation."""

    role: str = Field(
        ...,
        description="Message role (user or assistant)",
        pattern="^(user|assistant)$"
    )
    content: str = Field(
        ...,
        description="Message content",
        min_length=1
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the message was created"
    )


class ConversationSession(BaseModel):
    """Conversation session with message history."""

    session_id: UUID = Field(
        default_factory=uuid4,
        description="Unique session identifier"
    )
    messages: List[Message] = Field(
        default_factory=list,
        description="Conversation message history"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the session was created"
    )
    last_activity: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity timestamp"
    )

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation.

        Args:
            role: Message role (user or assistant)
            content: Message content
        """
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.last_activity = datetime.utcnow()

    def get_context_messages(self, max_messages: int = 10) -> List[dict]:
        """
        Get recent messages formatted for LLM context.

        Args:
            max_messages: Maximum number of messages to return

        Returns:
            List of message dictionaries with role and content
        """
        recent_messages = self.messages[-max_messages:]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
        ]


class SessionResponse(BaseModel):
    """Response model for session information."""

    session_id: UUID
    message_count: int
    created_at: datetime
    last_activity: datetime
