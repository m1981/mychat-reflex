"""
Chat State - UI Controller for Chat Feature.

Architectural Rules Applied:
1. ViewModel Pattern: This class only manages UI state and delegates business logic to Use Cases.
2. Dependency Injection (ADR 015): Resolves ILLMService via AppContainer Factory, removing vendor lock-in.
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
from .use_cases import SendMessageUseCase, LoadHistoryUseCase, PrepRegenerationUseCase

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

    # Inline Edit State
    editing_message_id: str = ""
    edit_content: str = ""

    # Destructive Action Warning State
    show_truncate_warning: bool = False
    pending_regenerate_id: str = ""

    # UI preferences (LocalStorage)
    selected_model: str = rx.LocalStorage("claude-sonnet-4-5")
    temperature: str = rx.LocalStorage("0.7")
    enable_reasoning: str = rx.LocalStorage("false")
    reasoning_budget: str = rx.LocalStorage("2000")
    code_theme: str = rx.LocalStorage("nord")
    light_code_theme: str = rx.LocalStorage("github-light")

    # Explicit setters for LocalStorage fields
    def set_selected_model(self, value):
        logger.info(f"[ChatState.set_selected_model] ✅ New selected_model={value!r}")
        self.selected_model = str(value)

    def set_temperature(self, value):
        self.temperature = str(value)

    def set_enable_reasoning(self, value):
        self.enable_reasoning = str(value).lower()

    def set_reasoning_budget(self, value):
        self.reasoning_budget = str(value)

    def set_code_theme(self, value):
        self.code_theme = str(value)

    def set_light_code_theme(self, value):
        self.light_code_theme = str(value)

    # ========================================================================
    # TYPE CONVERSION COMPUTED VARS
    # ========================================================================

    @rx.var
    def temperature_float(self) -> float:
        try:
            return float(self.temperature)
        except (ValueError, TypeError):
            return 0.7

    @rx.var
    def enable_reasoning_bool(self) -> bool:
        return str(self.enable_reasoning).lower() in ("true", "1", "yes")

    @rx.var
    def reasoning_budget_int(self) -> int:
        try:
            return int(self.reasoning_budget)
        except (ValueError, TypeError):
            return 2000

    # ========================================================================
    # UI DISPLAY COMPUTED VARS
    # ========================================================================

    @rx.var
    def active_code_theme(self) -> str:
        return self.code_theme

    @rx.var
    def model_display_name(self) -> str:
        model_names = {
            "claude-sonnet-4-5": "Claude Sonnet 4.5",
            "claude-sonnet-4": "Claude Sonnet 4",
            "claude-opus-4": "Claude Opus 4",
            "gpt-4o": "GPT-4o",
            "gpt-4o-mini": "GPT-4o Mini",
            "o1": "OpenAI o1",
            "o1-mini": "OpenAI o1 Mini",
        }
        model = str(self.selected_model)
        return model_names.get(model, model)

    @rx.var
    def current_chat(self) -> Optional[Conversation]:
        for chat in self.chats:
            if chat.id == self.current_conversation_id:
                return chat
        return None

    @rx.var
    def filtered_folders(self) -> list[ChatFolder]:
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
        logger.info(f"[ChatState.on_load] Current is_generating={self.is_generating}")
        logger.info("=" * 80)

        # Reset generating state on page load (in case of interrupted background tasks)
        if self.is_generating:
            logger.warning("[ChatState.on_load] ⚠️ Resetting is_generating from True to False")
            self.is_generating = False

        use_case = LoadHistoryUseCase()
        with rx.session() as session:
            db_messages = await use_case.execute(session, self.current_conversation_id)
            self.messages = [Message(**m.model_dump()) for m in db_messages]

        with rx.session() as session:
            db_folders = session.query(ChatFolder).all()
            db_chats = session.query(Conversation).all()
            self.folders = [ChatFolder(**f.model_dump()) for f in db_folders]
            self.chats = [Conversation(**c.model_dump()) for c in db_chats]
        
        logger.info(f"[ChatState.on_load] ✅ Loaded {len(self.messages)} messages, {len(self.chats)} chats")

    # ========================================================================
    # UI EVENT HANDLERS (Synchronous / Fast Async)
    # ========================================================================

    def set_input_text(self, value: str):
        self.input_text = value

    def set_sidebar_search(self, value: str):
        self.sidebar_search = value

    async def select_chat(self, chat_id: str):
        self.current_conversation_id = chat_id
        for chat in self.chats:
            if chat.id == chat_id:
                self.current_chat_title = chat.title
                break

        use_case = LoadHistoryUseCase()
        with rx.session() as session:
            db_messages = await use_case.execute(session, chat_id)
            self.messages = [Message(**m.model_dump()) for m in db_messages]

    def create_new_chat(self):
        new_id = str(uuid4())
        new_chat = Conversation(id=new_id, title="New Chat")

        with rx.session() as session:
            session.add(Conversation(**new_chat.model_dump()))
            session.commit()

        self.chats.append(new_chat)
        self.chats = self.chats
        self.current_conversation_id = new_id
        self.current_chat_title = "New Chat"
        self.messages = []

    def create_new_folder(self):
        new_id = str(uuid4())
        new_folder = ChatFolder(id=new_id, name="New Folder")

        with rx.session() as session:
            session.add(ChatFolder(**new_folder.model_dump()))
            session.commit()

        self.folders.append(new_folder)
        self.folders = self.folders

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

        # Step 3: Stream LLM response
        logger.info("-" * 80)
        logger.info("[ChatState] STEP 3: Streaming LLM response")
        logger.info("-" * 80)

        # Get current model selection and config
        async with self:
            current_model = str(self.selected_model)
            current_temp = self.temperature_float
            current_reasoning = self.enable_reasoning_bool
            current_budget = self.reasoning_budget_int

        # ✅ THE CLEAN ARCHITECTURE FIX:
        # Ask the container for the service based on the string!
        llm_service = AppContainer.resolve_llm_service(current_model)
        use_case = SendMessageUseCase(llm_service)

        full_response = ""
        chat_history = self.messages[:-2]

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

                # Buffer to prevent React thrashing
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

            self.messages[-1].content = full_response
            self.is_generating = False
            self.messages = self.messages

        logger.info("[ChatState] ✅ HANDLE_SEND_MESSAGE COMPLETED")

    # ========================================================================
    # MESSAGE ACTIONS (Copy, Delete, Regenerate)
    # ========================================================================

    def copy_message(self, message_id: str):
        """Copy message content to clipboard and show a toast."""
        # Find the message in memory (O(N) is fine for chat history)
        message = next((m for m in self.messages if m.id == message_id), None)

        if message:
            logger.info(f"[ChatState] Copied message {message_id} to clipboard.")
            # In Reflex, we return a list of events to execute in the browser
            return [
                rx.set_clipboard(message.content),
                rx.toast.success("Copied to clipboard!", position="bottom-right"),
            ]
        return rx.toast.error("Message not found.", position="bottom-right")

    def delete_message(self, message_id: str):
        """Delete a message from DB and UI."""
        if self.is_generating:
            return rx.toast.warning(
                "Cannot delete messages while AI is typing.", position="bottom-right"
            )

        logger.info(f"[ChatState] Deleting message: {message_id}")

        # 1. Delete from Database
        with rx.session() as session:
            message = session.query(Message).filter(Message.id == message_id).first()
            if message:
                session.delete(message)
                session.commit()

        # 2. Update UI State
        self.messages = [m for m in self.messages if m.id != message_id]
        return rx.toast.info("Message deleted.", position="bottom-right")

    # ========================================================================
    # INLINE EDITING
    # ========================================================================

    def start_edit(self, message_id: str, current_content: str):
        self.editing_message_id = message_id
        self.edit_content = current_content

    def cancel_edit(self):
        self.editing_message_id = ""
        self.edit_content = ""

    def save_edit(self):
        if not self.edit_content.strip():
            return rx.toast.error("Message cannot be empty.")

        with rx.session() as session:
            message = (
                session.query(Message)
                .filter(Message.id == self.editing_message_id)
                .first()
            )
            if message:
                message.content = self.edit_content
                session.commit()

        for m in self.messages:
            if m.id == self.editing_message_id:
                m.content = self.edit_content
                break

        self.messages = self.messages
        self.editing_message_id = ""

        return self.request_regenerate(self.editing_message_id)

    # ========================================================================
    # REGENERATE & TRUNCATE FLOW
    # ========================================================================

    def request_regenerate(self, message_id: str):
        logger.info("=" * 80)
        logger.info(f"[request_regenerate] 🔄 CALLED with message_id={message_id}")
        logger.info(f"[request_regenerate] Current is_generating={self.is_generating}")
        logger.info(f"[request_regenerate] Current messages count={len(self.messages)}")
        logger.info("=" * 80)
        
        if self.is_generating:
            logger.warning(f"[request_regenerate] ⚠️ BLOCKED: is_generating={self.is_generating}")
            return rx.toast.warning("Already generating a response.")

        target_idx = next(
            (i for i, m in enumerate(self.messages) if m.id == message_id), -1
        )
        if target_idx == -1:
            logger.error(f"[request_regenerate] ❌ Message not found: {message_id}")
            return rx.toast.error("Message not found.")

        target_msg = self.messages[target_idx]
        is_destructive = False

        logger.info(f"[request_regenerate] Target message index={target_idx}, role={target_msg.role}")
        logger.info(f"[request_regenerate] Total messages={len(self.messages)}")

        if target_msg.role == "assistant":
            if target_idx < len(self.messages) - 1:
                is_destructive = True
                logger.info(f"[request_regenerate] DESTRUCTIVE: Assistant message with {len(self.messages) - target_idx - 1} messages after it")
        else:
            if target_idx < len(self.messages) - 2:
                is_destructive = True
                logger.info(f"[request_regenerate] DESTRUCTIVE: User message with {len(self.messages) - target_idx - 2} messages after response")

        if is_destructive:
            logger.info(f"[request_regenerate] 🚨 DESTRUCTIVE PATH: Showing warning modal")
            self.pending_regenerate_id = message_id
            self.show_truncate_warning = True
        else:
            logger.info(f"[request_regenerate] ⚡ FAST PATH: Calling confirm_regenerate directly")
            # FAST PATH: Trigger regeneration immediately
            return ChatState.confirm_regenerate(message_id)

    def cancel_regenerate(self):
        logger.info("[cancel_regenerate] 🚫 User cancelled regeneration")
        self.show_truncate_warning = False
        self.pending_regenerate_id = ""

    @rx.event(background=True)
    async def confirm_regenerate(self, message_id: str = ""):
        """Execute the regeneration using pure Use Cases."""
        logger.info("=" * 80)
        logger.info(f"[confirm_regenerate] 🎬 BACKGROUND EVENT STARTED")
        logger.info(f"[confirm_regenerate] Received message_id={message_id!r}")
        logger.info("=" * 80)
        
        async with self:
            logger.info(f"[confirm_regenerate] Inside async context - is_generating={self.is_generating}")
            logger.info(f"[confirm_regenerate] pending_regenerate_id={self.pending_regenerate_id!r}")
            
            self.show_truncate_warning = False
            # Use the passed message_id, or fall back to pending_regenerate_id
            target_message_id = message_id or self.pending_regenerate_id
            self.pending_regenerate_id = ""
            
            logger.info(f"[confirm_regenerate] Resolved target_message_id={target_message_id!r}")
            
            if not target_message_id:
                logger.error("[confirm_regenerate] ❌ No message ID available!")
                yield rx.toast.error("No message ID provided for regeneration.")
                self.is_generating = False
                return
                
            logger.info(f"[confirm_regenerate] ✅ Setting is_generating=True")
            self.is_generating = True

        # 1. Execute Business Logic (DB Truncation) via Use Case
        logger.info(f"[confirm_regenerate] STEP 1: Executing PrepRegenerationUseCase")
        with rx.session() as session:
            prep_use_case = PrepRegenerationUseCase()
            try:
                new_ai_msg_id, prompt_text, truncated_history = prep_use_case.execute(
                    session, self.current_conversation_id, target_message_id
                )
                logger.info(f"[confirm_regenerate] ✅ Prep complete: new_ai_msg_id={new_ai_msg_id}")
                logger.info(f"[confirm_regenerate] Prompt text: {prompt_text[:100]}...")
                logger.info(f"[confirm_regenerate] Truncated history length: {len(truncated_history)}")
            except ValueError as e:
                logger.error(f"[confirm_regenerate] ❌ PrepRegenerationUseCase failed: {e}")
                yield rx.toast.error(str(e))
                async with self:
                    self.is_generating = False
                return

        # 2. Sync UI State with the truncated history
        logger.info(f"[confirm_regenerate] STEP 2: Syncing UI state")
        async with self:
            self.messages = [Message(**m.model_dump()) for m in truncated_history]
            logger.info(f"[confirm_regenerate] Messages after truncation: {len(self.messages)}")

            # Add the empty AI placeholder returned by the Use Case
            ai_msg = Message(
                id=new_ai_msg_id,
                conversation_id=self.current_conversation_id,
                role="assistant",
                content="",
            )
            self.messages.append(ai_msg)
            self.messages = self.messages
            logger.info(f"[confirm_regenerate] Added AI placeholder, total messages: {len(self.messages)}")

        # 3. Stream the new response (Reusing SendMessageUseCase)
        logger.info("[confirm_regenerate] STEP 3: Streaming regenerated response...")
        async with self:
            current_model = str(self.selected_model)
            current_temp = self.temperature_float
            current_reasoning = self.enable_reasoning_bool
            current_budget = self.reasoning_budget_int
            logger.info(f"[confirm_regenerate] Model config: {current_model}, temp={current_temp}, reasoning={current_reasoning}")

        llm_service = AppContainer.resolve_llm_service(current_model)
        stream_use_case = SendMessageUseCase(llm_service)

        full_response = ""
        chat_history = self.messages[:-2]
        logger.info(f"[confirm_regenerate] Chat history for LLM: {len(chat_history)} messages")

        async for chunk in stream_use_case.execute(
                conversation_id=self.current_conversation_id,
                user_message=prompt_text,
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

                if len(char_buffer) >= 40:
                    async with self:
                        self.messages[-1].content = _close_open_code_block(full_response)
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

        # 4. Save final message
        logger.info(f"[confirm_regenerate] STEP 4: Saving final message (length={len(full_response)})")
        async with self:
            with rx.session() as session:
                # Fetch the placeholder we created in the Prep Use Case and update it
                ai_msg_final = session.query(Message).filter(Message.id == new_ai_msg_id).first()
                if ai_msg_final:
                    ai_msg_final.content = full_response
                    logger.info(f"[confirm_regenerate] ✅ Updated DB message {new_ai_msg_id}")
                else:
                    logger.error(f"[confirm_regenerate] ❌ Could not find message {new_ai_msg_id} in DB!")

                conversation = session.query(Conversation).filter(
                    Conversation.id == self.current_conversation_id).first()
                if conversation:
                    conversation.updated_at = datetime.now(timezone.utc)
                session.commit()

            self.messages[-1].content = full_response
            logger.info(f"[confirm_regenerate] ✅ Setting is_generating=False")
            self.is_generating = False
            self.messages = self.messages

        logger.info("=" * 80)
        logger.info("[confirm_regenerate] ✅ REGENERATE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
