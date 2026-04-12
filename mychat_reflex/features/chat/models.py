"""
Chat feature models - Unified rx.Model approach.
"""

import reflex as rx
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field  # Required for database constraints and dynamic defaults


class Message(rx.Model, table=True):
    """Unified Message model."""

    # Primary key (Must explicitly state primary_key=True since it's a string/UUID)
    id: str = Field(primary_key=True)

    # Foreign key (Must explicitly tell the database it references conversation.id)
    conversation_id: str = Field(foreign_key="conversation.id")

    # Core message fields
    role: str  # "user" | "assistant" | "system"
    content: str

    # CRITICAL FIX: Use default_factory so the time is generated dynamically on insert!
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Optional metadata
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
        # Format: "6:15 PM 30 Mar 2026"
        return self.created_at.strftime("%I:%M %p %d %b %Y")

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id}, role={self.role}, content={self.content[:30]}...)>"
        )


class Conversation(rx.Model, table=True):
    """Unified Conversation model."""

    # Primary key
    id: str = Field(primary_key=True)

    # Core fields
    title: str = "New Chat"

    # Foreign key to ChatFolder
    folder_id: Optional[str] = Field(default=None, foreign_key="chatfolder.id")

    # CRITICAL FIX: Dynamic timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_in_folder(self) -> bool:
        return self.folder_id is not None

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"


class ChatFolder(rx.Model, table=True):
    """Unified ChatFolder model."""

    # Primary key
    id: str = Field(primary_key=True)

    # Core fields
    name: str

    # CRITICAL FIX: Dynamic timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<ChatFolder(id={self.id}, name={self.name})>"
