"""
Chat State - UI Controller for Chat Feature.

Architectural Rules Applied:
1. ViewModel Pattern: This class only manages UI state and delegates business logic to Use Cases.
2. Dependency Injection (ADR 015): Resolves ILLMService via AppContainer, removing vendor lock-in.
3. WebSocket Buffering (ADR 002-V2): Batches LLM chunks before yielding to prevent UI freezing.
4. Safe DB Sessions: rx.session() is opened, passed to Use Cases, and closed immediately.
"""

import logging
import reflex as rx
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
import asyncio

from mychat_reflex.core.di import AppContainer
from mychat_reflex.core.llm_ports import LLMConfig
from .models import Message, Conversation, ChatFolder
from .use_cases import SendMessageUseCase, LoadHistoryUseCase

logger = logging.getLogger(__name__)


def _close_open_code_block(content: str) -> str:
    """Append a closing ``` when content has an unclosed fenced code block.
    Prevents react-markdown from parsing # comments as headings mid-stream."""
    return content + "\n```" if content.count("```") % 2 == 1 else content


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
    - WebSocket updates to frontend (with buffering)
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
    selected_model: str = "Claude Sonnet 4.5"
    code_theme: str = rx.LocalStorage("nord", name="code_theme_v2")
    light_code_theme: str = rx.LocalStorage("github-light", name="light_code_theme_v2")

    def set_code_theme(self, theme: str):
        self.code_theme = theme

    def set_light_code_theme(self, theme: str):
        self.light_code_theme = theme

    @rx.var
    def active_code_theme(self) -> str:
        """Compile-safe active code theme.

        Note: server-side compile does not always expose frontend color mode,
        so default to dark theme here to avoid compile-time attribute errors.
        """
        return self.code_theme

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

    async def on_load(self):
        """Load data when page loads."""
        logger.info("[ChatState] on_load triggered")

        # Load messages using the pure Use Case
        use_case = LoadHistoryUseCase()
        with rx.session() as session:
            db_messages = await use_case.execute(session, self.current_conversation_id)
            # ✅ CRITICAL FIX: Clone into pure in-memory objects
            self.messages = [Message(**m.model_dump()) for m in db_messages]

        # Load sidebar data
        with rx.session() as session:
            db_folders = session.query(ChatFolder).all()
            db_chats = session.query(Conversation).all()
            # ✅ CRITICAL FIX: Clone into pure in-memory objects
            self.folders = [ChatFolder(**f.model_dump()) for f in db_folders]
            self.chats = [Conversation(**c.model_dump()) for c in db_chats]

    # ========================================================================
    # UI EVENT HANDLERS (Synchronous / Fast Async)
    # ========================================================================

    def set_input_text(self, value: str):
        self.input_text = value

    def set_sidebar_search(self, value: str):
        self.sidebar_search = value

    async def select_chat(self, chat_id: str):
        """Select a different conversation."""
        logger.info(f"[ChatState] Selecting chat: {chat_id}")

        self.current_conversation_id = chat_id

        # Update title
        for chat in self.chats:
            if chat.id == chat_id:
                self.current_chat_title = chat.title
                break

        # Load messages using the pure Use Case
        use_case = LoadHistoryUseCase()
        with rx.session() as session:
            db_messages = await use_case.execute(session, chat_id)
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
        logger.info("=" * 80)
        logger.info("[ChatState] 🎯 HANDLE_SEND_MESSAGE TRIGGERED")
        logger.info("=" * 80)

        async with self:
            prompt = self.input_text

            if not prompt.strip() or self.is_generating:
                logger.warning(
                    "[ChatState] ⚠️ Aborting: Empty prompt or already generating"
                )
                return

        # Step 1: Save user message
        logger.info("[ChatState] STEP 1: Saving user message")
        user_msg_id = str(uuid4())
        async with self:
            self.input_text = ""
            self.is_generating = True

            user_msg = Message(
                id=user_msg_id,
                conversation_id=self.current_conversation_id,
                role="user",
                content=prompt,
                avatar_url="https://i.pravatar.cc/150?img=11",
            )

            with rx.session() as session:
                session.add(Message(**user_msg.model_dump()))
                session.commit()

            self.messages.append(user_msg)
            self.messages = self.messages

        # Step 2: Create AI message placeholder
        logger.info("[ChatState] STEP 2: Creating AI message placeholder")
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

        # Step 3: Stream LLM response (WITH TYPEWRITER EFFECT)
        logger.info("-" * 80)
        logger.info("[ChatState] STEP 3: Streaming LLM response")
        logger.info("-" * 80)

        llm_service = AppContainer.resolve_llm_service()
        use_case = SendMessageUseCase(llm_service)

        full_response = ""
        chat_history = self.messages[:-2]

        async for chunk in use_case.execute(
            conversation_id=self.current_conversation_id,
            user_message=prompt,
            history=chat_history,
            config=LLMConfig(temperature=0.7),
        ):
            char_buffer = ""

            for char in chunk:
                char_buffer += char
                full_response += char

                if len(char_buffer) >= 12:
                    async with self:
                        self.messages[-1].content = _close_open_code_block(
                            full_response
                        )
                        self.messages = self.messages
                    yield
                    await asyncio.sleep(0.01)
                    char_buffer = ""

            if char_buffer:
                async with self:
                    self.messages[-1].content = _close_open_code_block(full_response)
                    self.messages = self.messages
                yield
                await asyncio.sleep(0.01)

        # Step 4: Save final AI message
        logger.info("[ChatState] STEP 4: Saving final AI message to database")
        async with self:
            with rx.session() as session:
                ai_msg_final = Message(
                    id=ai_msg_id,
                    conversation_id=self.current_conversation_id,
                    role="assistant",
                    content=full_response,
                )
                session.add(ai_msg_final)

                conversation = (
                    session.query(Conversation)
                    .filter(Conversation.id == self.current_conversation_id)
                    .first()
                )
                if conversation:
                    conversation.updated_at = datetime.now(timezone.utc)

                session.commit()

            # Restore clean content (no appended ```) now that streaming is complete
            self.messages[-1].content = full_response
            self.is_generating = False
            self.messages = self.messages

        logger.info("[ChatState] ✅ HANDLE_SEND_MESSAGE COMPLETED SUCCESSFULLY")

    # ========================================================================
    # PLACEHOLDER METHODS (Future Implementation)
    # ========================================================================

    def copy_message(self, message_id: str):
        pass

    def regenerate_message(self, message_id: str):
        pass
