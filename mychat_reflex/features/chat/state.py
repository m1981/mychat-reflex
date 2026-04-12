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

Migrated from mychat_reflex/state/chat_state.py (Phase 4, Task 4.1)
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
        """Get or create the LLM service instance."""
        if self._llm_service is None:
            self._llm_service = AnthropicAdapter(
                api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                model="claude-sonnet-4-20250514",
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
        """
        Load data when page loads.

        This runs on every page load/refresh.
        Loads conversation history and sidebar data.
        """
        logger.info("[ChatState] on_load triggered")

        # Load messages for current conversation
        with rx.session() as session:
            messages = (
                session.query(Message)
                .filter(Message.conversation_id == self.current_conversation_id)
                .order_by(Message.created_at)
                .all()
            )
            self.messages = messages
            logger.info(f"[ChatState] Loaded {len(messages)} messages")

        # Load folders and conversations
        with rx.session() as session:
            folders = session.query(ChatFolder).all()
            chats = session.query(Conversation).all()
            self.folders = folders
            self.chats = chats
            logger.info(
                f"[ChatState] Loaded {len(folders)} folders, {len(chats)} chats"
            )

    # ========================================================================
    # UI EVENT HANDLERS (Synchronous)
    # ========================================================================

    def set_input_text(self, value: str):
        """Update the input text."""
        self.input_text = value

    def set_sidebar_search(self, value: str):
        """Update sidebar search."""
        self.sidebar_search = value

    def select_chat(self, chat_id: str):
        """
        Select a different conversation.

        This loads the conversation's messages from the database.
        """
        logger.info(f"[ChatState] Selecting chat: {chat_id}")

        self.current_conversation_id = chat_id

        # Update title
        for chat in self.chats:
            if chat.id == chat_id:
                self.current_chat_title = chat.title
                break

        # Load messages
        with rx.session() as session:
            messages = (
                session.query(Message)
                .filter(Message.conversation_id == chat_id)
                .order_by(Message.created_at)
                .all()
            )
            self.messages = messages
            logger.info(f"[ChatState] Loaded {len(messages)} messages for {chat_id}")

    def create_new_chat(self):
        """Create a new conversation."""
        logger.info("[ChatState] Creating new chat")

        new_id = str(uuid4())
        new_chat = Conversation(id=new_id, title="New Chat")

        # Save to database
        with rx.session() as session:
            session.add(new_chat)
            session.commit()
            logger.info(f"[ChatState] Created conversation: {new_id}")

        # Update UI state
        self.chats.append(new_chat)
        self.chats = self.chats  # Trigger reactivity
        self.current_conversation_id = new_id
        self.current_chat_title = "New Chat"
        self.messages = []

    def create_new_folder(self):
        """Create a new folder."""
        logger.info("[ChatState] Creating new folder")

        new_id = str(uuid4())
        new_folder = ChatFolder(id=new_id, name="New Folder")

        # Save to database
        with rx.session() as session:
            session.add(new_folder)
            session.commit()
            logger.info(f"[ChatState] Created folder: {new_id}")

        # Update UI state
        self.folders.append(new_folder)
        self.folders = self.folders  # Trigger reactivity

    def delete_message(self, message_id: str):
        """Delete a message."""
        logger.info(f"[ChatState] Deleting message: {message_id}")

        # Delete from database
        with rx.session() as session:
            message = session.query(Message).filter(Message.id == message_id).first()
            if message:
                session.delete(message)
                session.commit()
                logger.info(f"[ChatState] Deleted message: {message_id}")

        # Update UI state
        self.messages = [m for m in self.messages if m.id != message_id]

    # ========================================================================
    # CORE CHAT FUNCTIONALITY (Async with @rx.background)
    # ========================================================================

    @rx.event(background=True)
    async def handle_send_message(self):
        """
        Handle sending a message and streaming AI response.

        CRITICAL: This follows Reflex's async rules!
        1. Use @rx.event(background=True) decorator
        2. Use 'async with self:' to safely update state
        3. Do NOT hold rx.session() during LLM streaming
        4. Use self.messages = self.messages to trigger reactivity

        Flow:
        1. Save user message (open session, write, close)
        2. Stream LLM response (NO session open!)
        3. Save AI message (open NEW session, write, close)
        """
        # Get prompt before clearing input
        async with self:
            prompt = self.input_text
            if not prompt.strip() or self.is_generating:
                logger.warning("[ChatState] Empty prompt or already generating")
                return

            logger.info(f"[ChatState] handle_send_message: {prompt[:50]}...")

        # Step 1: Save user message (open session, write, close)
        user_msg_id = str(uuid4())
        async with self:
            self.input_text = ""  # Clear input immediately
            self.is_generating = True

            user_msg = Message(
                id=user_msg_id,
                conversation_id=self.current_conversation_id,
                role="user",
                content=prompt,
                avatar_url="https://i.pravatar.cc/150?img=11",
            )

            # Save to database
            with rx.session() as session:
                session.add(user_msg)
                session.commit()
                logger.info(f"[ChatState] Saved user message: {user_msg_id}")

            # Update UI
            self.messages.append(user_msg)
            self.messages = self.messages  # CRITICAL: Trigger reactivity!

        # Step 2: Create AI message placeholder
        ai_msg_id = str(uuid4())
        async with self:
            ai_msg = Message(
                id=ai_msg_id,
                conversation_id=self.current_conversation_id,
                role="assistant",
                content="",  # Empty placeholder
            )

            # Add to UI immediately (optimistic update)
            self.messages.append(ai_msg)
            self.messages = self.messages  # CRITICAL: Trigger reactivity!

        # Step 3: Stream LLM response (NO database session open!)
        use_case = SendMessageUseCase(self._get_llm_service())
        full_response = ""

        logger.info("[ChatState] Starting LLM stream...")
        chunk_count = 0

        async for chunk in use_case.execute(
            conversation_id=self.current_conversation_id,
            user_message=prompt,
            config=LLMConfig(temperature=0.7),
        ):
            chunk_count += 1
            full_response += chunk

            # Update UI with streaming text
            async with self:
                # Find the AI message and update its content
                for i, msg in enumerate(self.messages):
                    if msg.id == ai_msg_id:
                        self.messages[i].content = full_response
                        self.messages = self.messages  # CRITICAL: Trigger reactivity!
                        break

        logger.info(f"[ChatState] LLM stream complete. Chunks: {chunk_count}")

        # Step 4: Save final AI message (open NEW session, write, close)
        async with self:
            # Update the AI message with final content
            for i, msg in enumerate(self.messages):
                if msg.id == ai_msg_id:
                    self.messages[i].content = full_response
                    break

            # Save to database
            with rx.session() as session:
                ai_msg_final = Message(
                    id=ai_msg_id,
                    conversation_id=self.current_conversation_id,
                    role="assistant",
                    content=full_response,
                )
                session.add(ai_msg_final)
                session.commit()
                logger.info(f"[ChatState] Saved AI message: {ai_msg_id}")

            # Update conversation timestamp
            with rx.session() as session:
                conversation = (
                    session.query(Conversation)
                    .filter(Conversation.id == self.current_conversation_id)
                    .first()
                )
                if conversation:
                    conversation.updated_at = datetime.now(timezone.utc)
                    session.commit()

            self.is_generating = False
            self.messages = self.messages  # Final reactivity trigger
            logger.info("[ChatState] handle_send_message complete")

    # ========================================================================
    # PLACEHOLDER METHODS (Future Implementation)
    # ========================================================================

    def copy_message(self, message_id: str):
        """Copy message to clipboard (placeholder)."""
        logger.info(f"[ChatState] copy_message: {message_id} (not implemented)")
        pass

    def regenerate_message(self, message_id: str):
        """Regenerate an AI response (placeholder)."""
        logger.info(f"[ChatState] regenerate_message: {message_id} (not implemented)")
        pass
