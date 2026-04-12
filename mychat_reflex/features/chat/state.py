"""
Chat State - UI Controller for Chat Feature.

This module contains ChatState (rx.State) which:
1. Manages UI state (input_text, is_generating, messages)
2. Orchestrates use cases (SendMessageUseCase, LoadHistoryUseCase)
3. Handles rx.session() safely (short-lived sessions)
4. Pushes WebSocket updates to frontend

CRITICAL REFLEX RULES APPLIED:
- @rx.event(background=True) decorator for async LLM operations
- async with self: for all state mutations
- self.messages = self.messages to trigger reactivity
- Open rx.session(), write, close immediately (NEVER hold during LLM streaming)
- Pydantic Cloning: .model_dump() used to prevent DetachedInstanceError
"""

import logging
import os
import reflex as rx
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from mychat_reflex.core.llm_ports import AnthropicAdapter, ILLMService, LLMConfig
from .models import Message, Conversation, ChatFolder
from .use_cases import SendMessageUseCase

logger = logging.getLogger(__name__)


# ============================================================================
# CHAT STATE (UI CONTROLLER)
# ============================================================================


class ChatState(rx.State):
    """
    Chat State - The UI Controller.

    Responsibilities:
    - UI state management (input_text, is_generating)
    - Database session management (rx.session() safety)
    - Use case orchestration (calls SendMessageUseCase)
    - WebSocket updates to frontend

    IMPORTANT: This follows Reflex's async rules!
    - @rx.event(background=True) for async operations
    - async with self: for state mutations
    - Short-lived rx.session() (never held during LLM streaming)
    """

    # ========================================================================
    # UI STATE (Sent to Browser)
    # ========================================================================

    # Current conversation
    current_conversation_id: str = "default-chat"
    current_chat_title: str = "New Chat"

    # Messages in current conversation
    messages: list[Message] = []

    # Input state
    input_text: str = ""
    is_generating: bool = False

    # Sidebar state
    sidebar_search: str = ""
    folders: list[ChatFolder] = []
    chats: list[Conversation] = []

    # UI preferences
    selected_model: str = "Claude Sonnet 4"

    # ========================================================================
    # BACKEND-ONLY STATE (Not Sent to Browser)
    # ========================================================================

    # LLM service instance (prefixed with _ so Reflex doesn't serialize it)
    # Initialized lazily to avoid pickling issues with AsyncAnthropic client
    _llm_service: Optional[AnthropicAdapter] = None

    def _get_llm_service(self) -> ILLMService:
        """
        Get or create the LLM service instance (lazy initialization).

        ARCHITECT NOTE: We cache this on `self._llm_service` for reuse.
        The underscore prefix prevents Reflex from serializing it to the frontend.
        """
        if self._llm_service is None:
            self._llm_service = AnthropicAdapter(
                api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                model="claude-sonnet-4-5",
            )
        return self._llm_service

    # ========================================================================
    # COMPUTED PROPERTIES
    # ========================================================================

    @rx.var
    def current_chat(self) -> Optional[Conversation]:
        """Get the current conversation object."""
        for chat in self.chats:
            if chat.id == self.current_conversation_id:
                return chat
        return None

    @rx.var
    def filtered_folders(self) -> list[ChatFolder]:
        """Filter folders based on search."""
        if not self.sidebar_search:
            return self.folders
        search_lower = self.sidebar_search.lower()
        return [f for f in self.folders if search_lower in f.name.lower()]

    # ========================================================================
    # LIFECYCLE METHODS
    # ========================================================================

    def on_load(self):
        """Load data when page loads."""
        logger.info("[ChatState] on_load triggered")

        # Load messages for current conversation
        with rx.session() as session:
            db_messages = (
                session.query(Message)
                .filter(Message.conversation_id == self.current_conversation_id)
                .order_by(Message.created_at)
                .all()
            )
            # ✅ CRITICAL FIX: Clone into pure in-memory objects
            self.messages = [Message(**m.model_dump()) for m in db_messages]

        with rx.session() as session:
            db_folders = session.query(ChatFolder).all()
            db_chats = session.query(Conversation).all()
            # ✅ CRITICAL FIX: Clone into pure in-memory objects
            self.folders = [ChatFolder(**f.model_dump()) for f in db_folders]
            self.chats = [Conversation(**c.model_dump()) for c in db_chats]

    # ========================================================================
    # UI EVENT HANDLERS (Synchronous)
    # ========================================================================

    def set_input_text(self, value: str):
        self.input_text = value

    def set_sidebar_search(self, value: str):
        self.sidebar_search = value

    def select_chat(self, chat_id: str):
        """Select a different conversation."""
        logger.info(f"[ChatState] Selecting chat: {chat_id}")

        self.current_conversation_id = chat_id

        # Update title
        for chat in self.chats:
            if chat.id == chat_id:
                self.current_chat_title = chat.title
                break

        # Load messages
        with rx.session() as session:
            db_messages = (
                session.query(Message)
                .filter(Message.conversation_id == chat_id)
                .order_by(Message.created_at)
                .all()
            )
            # ✅ CRITICAL FIX: Clone into pure in-memory objects
            self.messages = [Message(**m.model_dump()) for m in db_messages]

    def create_new_chat(self):
        """Create a new conversation."""
        logger.info("[ChatState] Creating new chat")
        new_id = str(uuid4())

        # 1. Create a pure in-memory object for the UI
        new_chat = Conversation(id=new_id, title="New Chat")

        # 2. Save a COPY to the database
        with rx.session() as session:
            session.add(Conversation(**new_chat.model_dump()))
            session.commit()

        # 3. Append the pure object to the state
        self.chats.append(new_chat)
        self.chats = self.chats
        self.current_conversation_id = new_id
        self.current_chat_title = "New Chat"
        self.messages = []

    def create_new_folder(self):
        """Create a new folder."""
        logger.info("[ChatState] Creating new folder")
        new_id = str(uuid4())

        # 1. Create a pure in-memory object for the UI
        new_folder = ChatFolder(id=new_id, name="New Folder")

        # 2. Save a COPY to the database
        with rx.session() as session:
            session.add(ChatFolder(**new_folder.model_dump()))
            session.commit()

        # 3. Append the pure object to the state
        self.folders.append(new_folder)
        self.folders = self.folders

    def delete_message(self, message_id: str):
        """Delete a message."""
        logger.info(f"[ChatState] Deleting message: {message_id}")

        with rx.session() as session:
            message = session.query(Message).filter(Message.id == message_id).first()
            if message:
                session.delete(message)
                session.commit()

        self.messages = [m for m in self.messages if m.id != message_id]

    # ========================================================================
    # CORE CHAT FUNCTIONALITY (Async with @rx.background)
    # ========================================================================

    @rx.event(background=True)
    async def handle_send_message(self):
        """Handle sending a message and streaming AI response."""
        async with self:
            prompt = self.input_text
            if not prompt.strip() or self.is_generating:
                return

        # Step 1: Save user message
        user_msg_id = str(uuid4())
        async with self:
            self.input_text = ""
            self.is_generating = True

            # Pure in-memory object
            user_msg = Message(
                id=user_msg_id,
                conversation_id=self.current_conversation_id,
                role="user",
                content=prompt,
                avatar_url="https://i.pravatar.cc/150?img=11",
            )

            # Save a COPY to the database
            with rx.session() as session:
                session.add(Message(**user_msg.model_dump()))
                session.commit()

            self.messages.append(user_msg)
            self.messages = self.messages

        # Step 2: Create AI message placeholder
        ai_msg_id = str(uuid4())
        async with self:
            ai_msg = Message(
                id=ai_msg_id,
                conversation_id=self.current_conversation_id,
                role="assistant",
                content="",
            )
            self.messages.append(ai_msg)
            self.messages = self.messages

        # Step 3: Stream LLM response
        use_case = SendMessageUseCase(self._get_llm_service())
        full_response = ""

        # Pass history to Use Case (excluding the new user msg and empty AI placeholder)
        chat_history = self.messages[:-2]

        async for chunk in use_case.execute(
            conversation_id=self.current_conversation_id,
            user_message=prompt,
            history=chat_history,
            config=LLMConfig(temperature=0.7),
        ):
            full_response += chunk
            async with self:
                # O(1) update: We know the AI message is the last one in the list
                self.messages[-1].content = full_response
                self.messages = self.messages

        # Step 4: Save final AI message
        async with self:
            with rx.session() as session:
                # Save a COPY of the final AI message to the database
                # CRITICAL FIX: Don't rely on .model_dump() - Reflex serialization breaks it
                # Just reconstruct from the variables we already have
                ai_msg_final = Message(
                    id=ai_msg_id,
                    conversation_id=self.current_conversation_id,
                    role="assistant",
                    content=full_response,
                )
                session.add(ai_msg_final)

                # Update conversation timestamp
                conversation = (
                    session.query(Conversation)
                    .filter(Conversation.id == self.current_conversation_id)
                    .first()
                )
                if conversation:
                    conversation.updated_at = datetime.now(timezone.utc)

                session.commit()

            self.is_generating = False
            self.messages = self.messages

    # ========================================================================
    # PLACEHOLDER METHODS (Future Implementation)
    # ========================================================================

    def copy_message(self, message_id: str):
        pass

    def regenerate_message(self, message_id: str):
        pass
