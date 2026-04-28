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

    # UI preferences (LocalStorage)
    # CRITICAL: Store everything as strings in LocalStorage, convert to proper types via computed vars
    # This avoids type mismatch errors during state hydration from browser
    selected_model: str = rx.LocalStorage("claude-sonnet-4-5")
    temperature: str = rx.LocalStorage("0.7")  # String, not float!
    enable_reasoning: str = rx.LocalStorage("false")  # String, not bool!
    reasoning_budget: str = rx.LocalStorage("2000")  # String, not int!
    code_theme: str = rx.LocalStorage("nord")
    light_code_theme: str = rx.LocalStorage("github-light")

    # Explicit setters for LocalStorage fields (required in Reflex 0.8.9+)
    # CRITICAL: Convert all values to strings for LocalStorage compatibility
    def set_selected_model(self, value):
        """Set the selected AI model."""
        logger.info(
            f"[ChatState.set_selected_model] 🔧 Called with value={value!r} (type={type(value).__name__})"
        )
        logger.info(
            f"[ChatState.set_selected_model] 📊 Current selected_model={self.selected_model!r} (type={type(self.selected_model).__name__})"
        )
        self.selected_model = str(value)
        logger.info(
            f"[ChatState.set_selected_model] ✅ New selected_model={self.selected_model!r} (type={type(self.selected_model).__name__})"
        )

    def set_temperature(self, value):
        """Set the temperature for AI responses."""
        logger.debug(
            f"[ChatState.set_temperature] 🔧 Called with value={value!r} (type={type(value).__name__})"
        )
        self.temperature = str(value)
        logger.debug(f"[ChatState.set_temperature] ✅ Set to {self.temperature!r}")

    def set_enable_reasoning(self, value):
        """Enable or disable extended reasoning mode."""
        logger.debug(
            f"[ChatState.set_enable_reasoning] 🔧 Called with value={value!r} (type={type(value).__name__})"
        )
        self.enable_reasoning = str(value).lower()  # Convert bool to 'true'/'false'
        logger.debug(
            f"[ChatState.set_enable_reasoning] ✅ Set to {self.enable_reasoning!r}"
        )

    def set_reasoning_budget(self, value):
        """Set the reasoning token budget."""
        logger.debug(
            f"[ChatState.set_reasoning_budget] 🔧 Called with value={value!r} (type={type(value).__name__})"
        )
        self.reasoning_budget = str(value)
        logger.debug(
            f"[ChatState.set_reasoning_budget] ✅ Set to {self.reasoning_budget!r}"
        )

    def set_code_theme(self, value):
        """Set the code highlighting theme."""
        logger.debug(
            f"[ChatState.set_code_theme] 🔧 Called with value={value!r} (type={type(value).__name__})"
        )
        self.code_theme = str(value)
        logger.debug(f"[ChatState.set_code_theme] ✅ Set to {self.code_theme!r}")

    def set_light_code_theme(self, value):
        """Set the light mode code highlighting theme."""
        logger.debug(
            f"[ChatState.set_light_code_theme] 🔧 Called with value={value!r} (type={type(value).__name__})"
        )
        self.light_code_theme = str(value)
        logger.debug(
            f"[ChatState.set_light_code_theme] ✅ Set to {self.light_code_theme!r}"
        )

    # ========================================================================
    # TYPE CONVERSION COMPUTED VARS (String LocalStorage → Typed Values)
    # ========================================================================

    @rx.var
    def temperature_float(self) -> float:
        """Get temperature as float for LLM config."""
        try:
            return float(self.temperature)
        except (ValueError, TypeError):
            return 0.7

    @rx.var
    def enable_reasoning_bool(self) -> bool:
        """Get reasoning enabled as bool."""
        return str(self.enable_reasoning).lower() in ("true", "1", "yes")

    @rx.var
    def reasoning_budget_int(self) -> int:
        """Get reasoning budget as int for comparisons."""
        try:
            return int(self.reasoning_budget)
        except (ValueError, TypeError):
            return 2000

    # ========================================================================
    # UI DISPLAY COMPUTED VARS
    # ========================================================================

    @rx.var
    def active_code_theme(self) -> str:
        """Compile-safe active code theme.

        Note: server-side compile does not always expose frontend color mode,
        so default to dark theme here to avoid compile-time attribute errors.
        """
        return self.code_theme

    @rx.var
    def model_display_name(self) -> str:
        """Get a friendly display name for the selected model."""
        model_names = {
            "claude-sonnet-4-5": "Claude Sonnet 4.5",
            "claude-sonnet-4": "Claude Sonnet 4",
            "claude-opus-4": "Claude Opus 4",
            "gpt-4o": "GPT-4o",
            "gpt-4o-mini": "GPT-4o Mini",
            "o1": "OpenAI o1",
            "o1-mini": "OpenAI o1 Mini",
        }
        # Access the actual value from LocalStorage
        model = str(self.selected_model)
        logger.debug(f"[model_display_name] 🏷️ Getting display name for model={model!r}")
        return model_names.get(model, model)

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
        logger.info("=" * 80)
        logger.info("[ChatState.on_load] 🚀 Page load triggered")
        logger.info("=" * 80)

        # Log LocalStorage values at startup
        logger.info("[ChatState.on_load] 📊 LocalStorage State:")
        logger.info(
            f"  - selected_model: {self.selected_model!r} (type={type(self.selected_model).__name__})"
        )
        logger.info(
            f"  - temperature: {self.temperature!r} (type={type(self.temperature).__name__})"
        )
        logger.info(
            f"  - enable_reasoning: {self.enable_reasoning!r} (type={type(self.enable_reasoning).__name__})"
        )
        logger.info(
            f"  - reasoning_budget: {self.reasoning_budget!r} (type={type(self.reasoning_budget).__name__})"
        )
        logger.info(
            f"  - code_theme: {self.code_theme!r} (type={type(self.code_theme).__name__})"
        )

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

        logger.info("[ChatState.on_load] ✅ Page load completed")

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

        # Get current model selection and config
        async with self:
            current_model = str(self.selected_model)
            current_temp = self.temperature_float
            current_reasoning = self.enable_reasoning_bool
            current_budget = self.reasoning_budget_int
            logger.info(
                f"[ChatState] 📊 Selected model: {current_model!r} (type={type(current_model).__name__})"
            )
            logger.info(
                f"[ChatState] 🌡️ Temperature: {current_temp!r} (type={type(current_temp).__name__})"
            )
            logger.info(
                f"[ChatState] 🧠 Reasoning enabled: {current_reasoning!r} (type={type(current_reasoning).__name__})"
            )
            logger.info(
                f"[ChatState] 💰 Reasoning budget: {current_budget!r} (type={type(current_budget).__name__})"
            )

        # Update DI container if model changed
        logger.info(
            f"[ChatState] 🔄 Ensuring correct adapter for model: {current_model}"
        )
        await self._ensure_correct_adapter(current_model)

        async for chunk in use_case.execute(
            conversation_id=self.current_conversation_id,
            user_message=prompt,
            history=chat_history,
            config=LLMConfig(
                temperature=current_temp,
                enable_reasoning=current_reasoning,
                reasoning_budget=current_budget,
            ),
        ):
            char_buffer = ""

            for char in chunk:
                char_buffer += char
                full_response += char

                # FIX: Increased buffer from 12 to 40 to prevent React thrashing
                if len(char_buffer) >= 40:
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

    # ========================================================================
    # MODEL ADAPTER MANAGEMENT
    # ========================================================================

    async def _ensure_correct_adapter(self, model):
        """Ensure the correct adapter is registered for the selected model."""
        import os
        from mychat_reflex.infrastructure.llm_adapters import (
            AnthropicAdapter,
            OpenAIAdapter,
        )

        logger.info(
            f"[_ensure_correct_adapter] 🔍 Checking adapter for model={model!r} (type={type(model).__name__})"
        )

        current_service = AppContainer.resolve_llm_service()
        current_model = getattr(current_service, "model", None)
        logger.info(
            f"[_ensure_correct_adapter] 📊 Current service model={current_model!r}"
        )

        # Convert model to string if needed (in case it's a LocalStorage proxy)
        model_str = str(model)
        logger.info(f"[_ensure_correct_adapter] 🔄 Converted to string: {model_str!r}")

        # Skip if already using the correct model
        if current_model == model_str:
            logger.info(
                f"[_ensure_correct_adapter] ✅ Already using {model_str}, no change needed"
            )
            return

        logger.info(
            f"[_ensure_correct_adapter] 🔄 Switching adapter from {current_model} to {model_str}"
        )

        # Determine which adapter to use
        if model_str.startswith(("claude", "sonnet", "opus")):
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            adapter = AnthropicAdapter(api_key=api_key, model=model_str)
            logger.info(
                f"[_ensure_correct_adapter] 🤖 Created AnthropicAdapter for {model_str}"
            )
        elif model_str.startswith(("gpt", "o1", "o3")):
            api_key = os.getenv("OPENAI_API_KEY", "")
            adapter = OpenAIAdapter(api_key=api_key, model=model_str)
            logger.info(
                f"[_ensure_correct_adapter] 🤖 Created OpenAIAdapter for {model_str}"
            )
        else:
            logger.warning(
                f"[_ensure_correct_adapter] ⚠️ Unknown model: {model_str}, keeping current adapter"
            )
            return

        # Register the new adapter
        AppContainer.register_llm_service(adapter)
        logger.info(
            f"[_ensure_correct_adapter] ✅ Successfully registered new adapter for {model_str}"
        )
