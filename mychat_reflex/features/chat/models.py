"""
Chat feature models - Unified rx.Model approach.

This module contains unified models that serve three purposes:
1. Database tables (SQLAlchemy ORM via Reflex)
2. Domain entities (business logic)
3. UI state variables (reactive state)

This eliminates the "Triple Model Tax" - one class instead of three!

Models:
- Message: Individual chat messages (user, assistant, system)
- Conversation: Chat sessions/conversations
- ChatFolder: Organizational folders (migrated from workspace feature for MVP simplicity)
"""

import reflex as rx
from datetime import datetime
from typing import Optional


class Message(rx.Model, table=True):
    """
    Unified Message model.

    Serves as:
    1. Database table (messages)
    2. Domain entity (business logic for chat messages)
    3. UI state variable (reactive display in Reflex)

    Migrated from:
    - src/core/database/models.py (Message ORM)
    - mychat_reflex/state/chat_state.py (Message Pydantic)

    Simplifications for MVP:
    - Content is string-only (no polymorphic TextPart/ImagePart/DocumentPart)
    - Removed Note relationship (will be added in future phase)
    """

    # Primary key
    id: str

    # Foreign key
    conversation_id: str

    # Core message fields
    role: str  # "user" | "assistant" | "system"
    content: str
    created_at: datetime = datetime.utcnow()

    # Optional metadata
    model_used: Optional[str] = None  # e.g., "claude-sonnet-4-5", "gpt-4o"
    avatar_url: Optional[str] = None  # User avatar URL

    @property
    def is_user(self) -> bool:
        """Computed property: Is this a user message?"""
        return self.role == "user"

    @property
    def is_assistant(self) -> bool:
        """Computed property: Is this an AI assistant message?"""
        return self.role == "assistant"

    @property
    def timestamp_formatted(self) -> str:
        """Computed property: Human-readable timestamp."""
        # Format: "6:15 PM 30 Mar 2026"
        return self.created_at.strftime("%I:%M %p %d %b %Y")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<Message(id={self.id}, role={self.role}, content={self.content[:30]}...)>"
        )


class Conversation(rx.Model, table=True):
    """
    Unified Conversation model.

    Serves as:
    1. Database table (conversations)
    2. Domain entity (chat session aggregate root)
    3. UI state variable (conversation metadata)

    Migrated from:
    - src/core/database/models.py (Conversation ORM)
    - mychat_reflex/state/chat_state.py (Chat Pydantic)

    Simplifications for MVP:
    - Removed explicit relationship to messages (query via conversation_id FK)
    - folder_id is nullable (conversations can exist without folders)
    """

    # Primary key
    id: str

    # Core fields
    title: str = "New Chat"
    folder_id: Optional[str] = None  # FK to ChatFolder (nullable)

    # Timestamps
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    @property
    def is_in_folder(self) -> bool:
        """Computed property: Is this conversation in a folder?"""
        return self.folder_id is not None

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Conversation(id={self.id}, title={self.title})>"


class ChatFolder(rx.Model, table=True):
    """
    Unified ChatFolder model.

    Serves as:
    1. Database table (chat_folders)
    2. Domain entity (folder organization)
    3. UI state variable (sidebar folders)

    Migrated from:
    - mychat_reflex/state/chat_state.py (ChatFolder Pydantic)

    Note: This is technically part of the workspace feature, but included here
    for MVP simplicity. Will be moved to features/workspace/models.py later.

    Simplifications for MVP:
    - No explicit chats list (query Conversations by folder_id)
    - No folder nesting (flat structure only)
    """

    # Primary key
    id: str

    # Core fields
    name: str
    created_at: datetime = datetime.utcnow()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<ChatFolder(id={self.id}, name={self.name})>"
