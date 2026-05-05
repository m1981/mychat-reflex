"""
Chat feature models - Unified rx.Model approach.
"""

import reflex as rx
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field


# CRITICAL FIX: Reflex/SQLModel cannot serialize lambda functions.
# We must use a named function for default_factory.
def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Message(rx.Model, table=True):
    """Unified Message model."""

    id: str = Field(primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id")
    role: str
    content: str

    # Fixed lambda bug
    created_at: datetime = Field(default_factory=get_utc_now)

    model_used: Optional[str] = None
    avatar_url: Optional[str] = None

    @property
    def is_user(self) -> bool:
        return self.role == "user"

    @property
    def is_assistant(self) -> bool:
        return self.role == "assistant"

    @property
    def timestamp_formatted(self) -> str:
        return self.created_at.strftime("%I:%M %p %d %b %Y")

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id}, role={self.role}, content={self.content[:30]}...)>"
        )


class Conversation(rx.Model, table=True):
    """Unified Conversation model."""

    id: str = Field(primary_key=True)
    title: str = "New Chat"
    folder_id: Optional[str] = Field(default=None, foreign_key="chatfolder.id")

    # Fixed lambda bug
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    @property
    def is_in_folder(self) -> bool:
        return self.folder_id is not None

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"


class ChatFolder(rx.Model, table=True):
    """Unified ChatFolder model."""

    id: str = Field(primary_key=True)
    name: str

    # Fixed lambda bug
    created_at: datetime = Field(default_factory=get_utc_now)

    def __repr__(self) -> str:
        return f"<ChatFolder(id={self.id}, name={self.name})>"
