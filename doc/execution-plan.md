<!--
LLM INSTRUCTION BLOCK
MOTIVATION: This is a TEMPORAL document. It acts as the Agile board, sprint tracker, and immediate context prompt for AI coding agents.
CONTENTS: Active sprint goals, refactoring tasks, test status, and commit hashes.
DO'S:
- DO update the "Status" and "Commits" lines immediately after completing an atomic task.
- DO read this file first to understand your current micro-goal before writing any code.
- DO strictly follow the Reflex-Specific Coding Rules (rx.background, async with self:, rx.session() safety).
DON'TS:
- DO NOT put permanent architectural decisions here (put them in docs/adr/).
- DO NOT skip the migration plan - follow the order strictly to avoid breaking the app.
-->

# 🏃‍♂️ Active Execution Plan - Reflex Monolith Migration

**Current Phase:** Major Architecture Refactor - FastAPI Backend → Reflex Full-Stack Monolith
**Overall Status:** Sprint 1 - Planning & Phase 1 Preparation

---

## 🎯 **Migration Strategy Overview**

We are refactoring from a **dual-backend architecture** (Reflex Frontend + FastAPI Backend) to a **Reflex full-stack monolith** to eliminate:
- ❌ HTTP/SSE parsing overhead
- ❌ Duplicate state management (ChatState + Backend State)
- ❌ Complex error handling across network boundary
- ❌ "Triple Model Tax" (UI models, Domain entities, ORM models)

**Target Architecture:**
- ✅ **Vertical Slice (Screaming) Architecture** - Group by feature, not technical layer
- ✅ **Unified Models** - `rx.Model` serves as Database Table + Domain Entity + UI State
- ✅ **Pure Use Cases** - Business logic depends on `ILLMService` interface (still clean!)
- ✅ **Reflex State as Controller** - Handles `rx.session()` + UI updates + Use Case orchestration

---

## 🏗️ **Target Folder Structure**

```
mychat_reflex/
 ├── mychat_reflex.py              # Main entry point (app definition)
 │
 ├── core/                          # Shared Infrastructure
 │    ├── database.py               # rx.Model base, Reflex DB config
 │    └── llm_ports.py              # ILLMService interface (from current src/core/domain/)
 │
 └── features/                      # VERTICAL SLICES (Screaming Architecture)
      │
      ├── chat/                     # Chat Bounded Context
      │    ├── models.py            # rx.Model: Conversation, Message (unified DB+Domain+UI)
      │    ├── use_cases.py         # SendMessageUseCase, LoadHistoryUseCase
      │    ├── state.py             # ChatState (rx.State - UI controller)
      │    └── ui.py                # chat_area(), message_bubble(), chat_input()
      │
      └── workspace/                # Sidebar/Folders Bounded Context
           ├── models.py            # rx.Model: ChatFolder
           ├── use_cases.py         # CreateFolderUseCase, MoveChatUseCase
           ├── state.py             # WorkspaceState
           └── ui.py                # sidebar(), folder_section()
```

**What gets REMOVED:**
- ❌ `src/` entire directory (FastAPI backend)
- ❌ `mychat_reflex/pages/` (merged into features/)
- ❌ `mychat_reflex/components/` (merged into features/)
- ❌ `mychat_reflex/state/chat_state.py` (refactored into features/chat/state.py)

---

## 📋 **Active Sprint 1: Foundation & Core Chat Migration**

**Goal:** Migrate the core chat functionality to the new Reflex monolith architecture while maintaining feature parity.

**Status:** 🚧 In Progress

---

### **Phase 1: Setup Core Infrastructure** ⚡ CRITICAL FOUNDATION

#### Task 1.1: Create New Folder Structure
*   **Status:** [x] COMPLETE
*   **Deliverables:**
    ```
    mychat_reflex/core/
    mychat_reflex/core/__init__.py
    mychat_reflex/core/database.py
    mychat_reflex/core/llm_ports.py
    mychat_reflex/features/
    mychat_reflex/features/__init__.py
    mychat_reflex/features/chat/
    mychat_reflex/features/chat/__init__.py
    mychat_reflex/features/workspace/
    mychat_reflex/features/workspace/__init__.py
    ```
*   **Completed:** 2026-04-12
*   **Files Created:**
    - `mychat_reflex/core/__init__.py` - Core module documentation
    - `mychat_reflex/core/database.py` - Placeholder for DB config
    - `mychat_reflex/core/llm_ports.py` - Placeholder for LLM interfaces
    - `mychat_reflex/features/__init__.py` - Features module documentation
    - `mychat_reflex/features/chat/__init__.py` - Chat feature documentation
    - `mychat_reflex/features/workspace/__init__.py` - Workspace feature documentation

#### Task 1.2: Migrate Core Interfaces (Ports)
*   **Status:** [ ] Not Started
*   **Source Files:**
    - `src/core/domain/entities.py` (Role, LLMConfig)
    - `src/core/domain/interfaces.py` (ILLMService)
    - `src/infrastructure/llm/anthropic_adapter.py`
    - `src/infrastructure/llm/openai_adapter.py`
*   **Target File:** `mychat_reflex/core/llm_ports.py`
*   **Changes Required:**
    1. Copy `Role` enum from `src/core/domain/entities.py`
    2. Copy `LLMConfig` from `src/core/domain/entities.py`
    3. Copy `ILLMService` interface from `src/core/domain/interfaces.py`
    4. Copy `AnthropicAdapter` and `OpenAIAdapter` (remove FastAPI dependencies)
    5. Remove multimodal content support (simplify to string-only for MVP)
*   **Testing:** Create `tests/test_llm_ports.py` with fake LLM adapter
*   **Commits:** `refactor: migrate LLM ports to Reflex core`

#### Task 1.3: Setup Reflex Database Configuration
*   **Status:** [ ] Not Started
*   **Target File:** `mychat_reflex/core/database.py`
*   **Implementation:**
    ```python
    import reflex as rx

    # Database configuration for Reflex
    # This will be the base for all rx.Model classes

    class DatabaseConfig:
        """Shared database configuration"""
        pass
    ```
*   **Documentation:** Add docstring explaining Reflex DB vs SQLAlchemy approach
*   **Commits:** `refactor: add Reflex database configuration`

---

### **Phase 2: Migrate Chat Models (Unified Approach)** 🎯

#### Task 2.1: Create Unified Message Model
*   **Status:** [ ] Not Started
*   **Source Files:**
    - `src/core/database/models.py` (Message ORM)
    - `mychat_reflex/state/chat_state.py` (Message Pydantic)
*   **Target File:** `mychat_reflex/features/chat/models.py`
*   **Implementation:**
    ```python
    import reflex as rx
    from typing import Optional
    from datetime import datetime

    class Message(rx.Model, table=True):
        """Unified Message model - DB Table + Domain Entity + UI State"""

        # Database fields (from src/core/database/models.py)
        id: str
        conversation_id: str
        role: str  # "user" | "assistant" | "system"
        content: str
        created_at: datetime = datetime.utcnow()
        model_used: Optional[str] = None

        # UI-specific fields (from mychat_reflex Message)
        is_user: bool  # Computed from role
        timestamp: str  # Formatted created_at
        avatar_url: Optional[str] = None
    ```
*   **Breaking Changes:**
    - Merge two separate Message classes into one
    - Remove polymorphic content (TextPart, ImagePart) for now
    - Add computed properties for UI fields
*   **Testing:** Unit tests for Message creation, validation
*   **Commits:** `refactor: create unified Message rx.Model`

#### Task 2.2: Create Unified Conversation Model
*   **Status:** [ ] Not Started
*   **Source Files:**
    - `src/core/database/models.py` (Conversation ORM)
    - `mychat_reflex/state/chat_state.py` (Chat Pydantic)
*   **Target File:** `mychat_reflex/features/chat/models.py`
*   **Implementation:**
    ```python
    class Conversation(rx.Model, table=True):
        """Unified Conversation model"""

        id: str
        title: str = "New Chat"
        folder_id: Optional[str] = None
        created_at: datetime = datetime.utcnow()
        updated_at: datetime = datetime.utcnow()

        # Relationships will be handled by Reflex ORM
    ```
*   **Testing:** Test conversation creation, folder assignment
*   **Commits:** `refactor: create unified Conversation rx.Model`

#### Task 2.3: Create ChatFolder Model
*   **Status:** [ ] Not Started
*   **Source:** `mychat_reflex/state/chat_state.py` (ChatFolder Pydantic)
*   **Target File:** `mychat_reflex/features/chat/models.py`
*   **Implementation:**
    ```python
    class ChatFolder(rx.Model, table=True):
        """Chat organization folders"""

        id: str
        name: str
        created_at: datetime = datetime.utcnow()
    ```
*   **Testing:** Test folder CRUD operations
*   **Commits:** `refactor: create ChatFolder rx.Model`

---

### **Phase 3: Migrate Use Cases (Pure Business Logic)** 🧠

#### Task 3.1: Create SendMessageUseCase (Reflex-native)
*   **Status:** [ ] Not Started
*   **Source File:** `src/features/chat/use_cases/send_message.py`
*   **Target File:** `mychat_reflex/features/chat/use_cases.py`
*   **Key Changes:**
    1. Remove `IConversationRepo` - direct `rx.session()` usage
    2. Remove `IVectorStore` - simplify to no RAG for MVP
    3. Keep `ILLMService` interface - PRESERVE CLEAN ARCHITECTURE
    4. Return `AsyncGenerator[str, None]` for streaming
*   **Implementation:**
    ```python
    from mychat_reflex.core.llm_ports import ILLMService, LLMConfig
    from .models import Message, Conversation
    import reflex as rx

    class SendMessageUseCase:
        def __init__(self, llm_service: ILLMService):
            self.llm = llm_service

        async def execute(
            self,
            conversation_id: str,
            user_message: str
        ) -> AsyncGenerator[str, None]:
            """
            Orchestrates sending a message and streaming AI response.

            IMPORTANT: This does NOT handle rx.session() - that's the State's job!
            Caller must handle database persistence.
            """
            # Stream from LLM
            async for chunk in self.llm.generate_stream(
                prompt=user_message,
                config=LLMConfig(temperature=0.7)
            ):
                yield chunk
    ```
*   **Reflex Rules Applied:**
    - ✅ Does NOT hold `rx.session()` during LLM call
    - ✅ Remains pure business logic
    - ✅ Depends on interface, not concrete adapter
*   **Testing:** Create `tests/test_send_message_use_case.py` with FakeLLM
*   **Commits:** `refactor: migrate SendMessageUseCase to Reflex`

#### Task 3.2: Create LoadHistoryUseCase
*   **Status:** [ ] Not Started
*   **Target File:** `mychat_reflex/features/chat/use_cases.py`
*   **Implementation:**
    ```python
    class LoadHistoryUseCase:
        async def execute(self, conversation_id: str) -> List[Message]:
            """Load conversation history from database"""
            # Direct rx.session() query
            with rx.session() as session:
                messages = session.query(Message).filter(
                    Message.conversation_id == conversation_id
                ).order_by(Message.created_at).all()
                return messages
    ```
*   **Commits:** `feat: add LoadHistoryUseCase`

---

### **Phase 4: Migrate ChatState (The Controller)** 🎮

#### Task 4.1: Create New ChatState in features/chat/state.py
*   **Status:** [ ] Not Started
*   **Source File:** `mychat_reflex/state/chat_state.py`
*   **Target File:** `mychat_reflex/features/chat/state.py`
*   **Key Responsibilities:**
    1. UI state management (input_text, is_generating)
    2. Database session management (`rx.session()` safety)
    3. Use Case orchestration (calls SendMessageUseCase)
    4. WebSocket updates to frontend
*   **Implementation Pattern:**
    ```python
    import reflex as rx
    from .models import Message, Conversation
    from .use_cases import SendMessageUseCase
    from mychat_reflex.core.llm_ports import AnthropicAdapter
    import os

    class ChatState(rx.State):
        # UI State
        messages: list[Message] = []
        input_text: str = ""
        is_generating: bool = False
        current_conversation_id: str = "default-chat"

        # Backend-only (not sent to browser)
        _llm_service: AnthropicAdapter = AnthropicAdapter(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        def on_load(self):
            """Load messages when page loads"""
            with rx.session() as session:
                self.messages = session.query(Message).filter(
                    Message.conversation_id == self.current_conversation_id
                ).all()

        @rx.background
        async def handle_send_message(self):
            """
            CRITICAL: This follows Reflex's async rules!
            1. Use @rx.background decorator
            2. Use 'async with self:' to safely update state
            3. Do NOT hold rx.session() during LLM streaming
            """
            prompt = self.input_text

            # Step 1: Save user message (open session, write, close)
            async with self:
                self.input_text = ""  # Clear input immediately
                self.is_generating = True

                user_msg = Message(
                    conversation_id=self.current_conversation_id,
                    role="user",
                    content=prompt,
                    is_user=True
                )

                with rx.session() as session:
                    session.add(user_msg)
                    session.commit()

                self.messages.append(user_msg)
                self.messages = self.messages  # CRITICAL: Trigger reactivity!

            # Step 2: Stream LLM response (NO database session open!)
            use_case = SendMessageUseCase(self._llm_service)
            full_response = ""

            async for chunk in use_case.execute(self.current_conversation_id, prompt):
                full_response += chunk

                # Update UI with streaming text
                async with self:
                    # Find the AI message placeholder and update it
                    # (You'll need to add placeholder logic)
                    pass

            # Step 3: Save AI message (open NEW session, write, close)
            async with self:
                ai_msg = Message(
                    conversation_id=self.current_conversation_id,
                    role="assistant",
                    content=full_response,
                    is_user=False
                )

                with rx.session() as session:
                    session.add(ai_msg)
                    session.commit()

                self.messages.append(ai_msg)
                self.messages = self.messages  # CRITICAL: Trigger reactivity!
                self.is_generating = False
    ```
*   **Reflex Rules Checklist:**
    - ✅ `@rx.background` decorator on async LLM methods
    - ✅ `async with self:` for all state mutations
    - ✅ `self.messages = self.messages` to trigger reactivity
    - ✅ Open `rx.session()`, write, close immediately
    - ✅ Do NOT hold session during LLM streaming
*   **Testing:** Integration test with FakeLLM
*   **Commits:** `refactor: migrate ChatState to features/chat/state.py`

---

### **Phase 5: Migrate UI Components** 🎨

#### Task 5.1: Create chat/ui.py with Core Components
*   **Status:** [ ] Not Started
*   **Source Files:**
    - `mychat_reflex/components/chat_area.py`
    - `mychat_reflex/components/message.py`
    - `mychat_reflex/components/chat_input.py`
*   **Target File:** `mychat_reflex/features/chat/ui.py`
*   **Changes:**
    1. Import from `.state` (ChatState)
    2. Import from `.models` (Message)
    3. Keep all UI component logic identical
    4. Remove cross-feature imports (sidebar goes to workspace/)
*   **Components to migrate:**
    - `message_bubble(message: Message)`
    - `chat_history()`
    - `chat_input()`
    - `chat_area()`
*   **Commits:** `refactor: migrate chat UI to features/chat/ui.py`

#### Task 5.2: Create workspace/ui.py for Sidebar
*   **Status:** [ ] Not Started
*   **Source File:** `mychat_reflex/components/sidebar.py`
*   **Target File:** `mychat_reflex/features/workspace/ui.py`
*   **Also create:**
    - `mychat_reflex/features/workspace/models.py` (ChatFolder)
    - `mychat_reflex/features/workspace/state.py` (WorkspaceState)
*   **Commits:** `refactor: create workspace feature slice`

---

### **Phase 6: Update Main Entry Point** 🚀

#### Task 6.1: Refactor mychat_reflex.py
*   **Status:** [ ] Not Started
*   **Current File:** `mychat_reflex/mychat_reflex.py`
*   **Changes:**
    ```python
    import reflex as rx
    from .features.chat.ui import chat_area
    from .features.workspace.ui import sidebar

    def index() -> rx.Component:
        """Main page - assemble features"""
        return rx.box(
            sidebar(),
            chat_area(),
            class_name="..."
        )

    app = rx.App()
    app.add_page(index, title="MyChat Reflex")
    ```
*   **Commits:** `refactor: update main entry point for vertical slices`

---

### **Phase 7: Database Migration** 🗄️

#### Task 7.1: Run Reflex Database Initialization
*   **Status:** [ ] Not Started
*   **Commands:**
    ```bash
    reflex db init
    reflex db migrate
    ```
*   **Verification:**
    - Check `alembic/versions/` for new migration
    - Verify tables: `conversations`, `messages`, `chat_folders`
*   **Commits:** `chore: initialize Reflex database`

#### Task 7.2: Data Migration Script (Optional)
*   **Status:** [ ] Not Started
*   **If needed:** Write script to migrate data from old `superchat.db` to new schema
*   **File:** `scripts/migrate_data.py`

---

### **Phase 8: Cleanup & Removal** 🧹

#### Task 8.1: Remove Old Backend (src/)
*   **Status:** [ ] Not Started
*   **Files to DELETE:**
    ```
    src/
    src/core/
    src/features/
    src/infrastructure/
    src/main.py
    ```
*   **Safety:** Git commit before deletion!
*   **Commands:**
    ```bash
    git add -A
    git commit -m "checkpoint: before removing FastAPI backend"
    rm -rf src/
    ```
*   **Commits:** `refactor: remove FastAPI backend`

#### Task 8.2: Remove Old Reflex Structure
*   **Status:** [ ] Not Started
*   **Files to DELETE:**
    ```
    mychat_reflex/components/
    mychat_reflex/pages/
    mychat_reflex/state/chat_state.py
    ```
*   **Commits:** `refactor: remove old component structure`

#### Task 8.3: Update pyproject.toml Dependencies
*   **Status:** [ ] Not Started
*   **Remove:**
    - `fastapi`
    - `uvicorn`
    - `httpx` (if only used for backend communication)
    - `anthropic` SDK (if now in core/llm_ports.py)
*   **Keep:**
    - `reflex`
    - `sqlalchemy` (Reflex uses it under the hood)
*   **Commits:** `chore: clean up dependencies`

---

### **Phase 9: Testing & Validation** ✅

#### Task 9.1: Write Integration Tests
*   **Status:** [ ] Not Started
*   **Test File:** `tests/integration/test_chat_feature.py`
*   **Test Cases:**
    1. User sends message → AI responds
    2. Message persistence in database
    3. Conversation history loading
    4. Streaming response handling
*   **Use:** Reflex testing utilities + FakeLLM
*   **Commits:** `test: add integration tests for chat feature`

#### Task 9.2: Manual Testing Checklist
*   **Status:** [ ] Not Started
*   **Steps:**
    1. [ ] Start app: `reflex run`
    2. [ ] Send a message - verify UI updates
    3. [ ] Check streaming works
    4. [ ] Refresh page - verify messages persist
    5. [ ] Create new chat
    6. [ ] Switch between chats
    7. [ ] Test folder organization
*   **Document:** Record any bugs in GitHub Issues

---

## 📦 **Backlog (Sprint 2+)**

*   **Sprint 2:** Add RAG Search (Vector Store integration in Reflex)
*   **Sprint 3:** Notes Feature (vertical slice: features/notes/)
*   **Sprint 4:** Multimodal Support (images, documents)
*   **Sprint 5:** Advanced Prompt Library
*   **Sprint 6:** Export/Import Functionality

---

## 🚨 **Critical Reflex Rules (NEVER FORGET!)**

### Rule 1: Reactivity Rule
```python
# ❌ WRONG - UI won't update!
self.messages.append(new_message)

# ✅ CORRECT - Triggers reactivity!
self.messages.append(new_message)
self.messages = self.messages
```

### Rule 2: Async Blocking Rule
```python
# ❌ WRONG - Blocks Reflex event loop!
def send_message(self):
    response = llm.generate(prompt)  # Synchronous LLM call

# ✅ CORRECT - Use background task!
@rx.background
async def send_message(self):
    async with self:
        # State updates here
        pass
```

### Rule 3: Session Rule
```python
# ❌ WRONG - Session held during LLM streaming!
with rx.session() as session:
    save_user_message()
    response = await llm.stream()  # 30 second stream!
    save_ai_message()

# ✅ CORRECT - Short-lived sessions!
with rx.session() as session:
    save_user_message()
# Session closed!
response = await llm.stream()
with rx.session() as session:
    save_ai_message()
```

### Rule 4: Context Locality Rule (Vertical Slices)
```python
# ❌ WRONG - Cross-domain imports!
from mychat_reflex.features.notes.models import Note  # In chat/state.py

# ✅ CORRECT - Stay within your slice!
from .models import Message  # In chat/state.py
```

---

## ✅ **Completed Tasks (Archive)**

*   None yet - starting fresh!

---

## 🎯 **Success Criteria for Sprint 1**

1. ✅ App runs with `reflex run` (no FastAPI needed!)
2. ✅ User can send messages and see AI responses
3. ✅ Messages persist in Reflex database
4. ✅ Streaming works in real-time
5. ✅ No `src/` directory remains
6. ✅ Code follows vertical slice architecture
7. ✅ All integration tests pass

---

**Last Updated:** 2026-04-12
**Next Review:** After Phase 1 completion
