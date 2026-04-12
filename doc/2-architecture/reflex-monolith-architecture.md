# Reflex Monolith Architecture Specification

**Document Status:** Active
**Last Updated:** 2026-04-12
**Architecture Pattern:** Vertical Slice (Screaming) Architecture + Clean Architecture (Hexagonal Ports & Adapters)

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    REFLEX MONOLITH                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Browser    │  │   Browser    │  │   Browser    │     │
│  │  (Client 1)  │  │  (Client 2)  │  │  (Client 3)  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │ WebSocket                      │
│                            ▼                                │
│         ┌──────────────────────────────────┐               │
│         │      Reflex Runtime              │               │
│         │   (State Sync via WebSockets)    │               │
│         └──────────────┬───────────────────┘               │
│                        │                                    │
│         ┌──────────────▼───────────────┐                   │
│         │      rx.State Controllers    │                   │
│         │  - ChatState                 │                   │
│         │  - WorkspaceState            │                   │
│         └──────────────┬───────────────┘                   │
│                        │                                    │
│         ┌──────────────▼───────────────┐                   │
│         │      Use Cases (Pure)        │                   │
│         │  - SendMessageUseCase        │                   │
│         │  - LoadHistoryUseCase        │                   │
│         └──────────────┬───────────────┘                   │
│                        │                                    │
│         ┌──────────────▼───────────────┐                   │
│         │   Adapters (Infrastructure)  │                   │
│         │  - AnthropicAdapter          │                   │
│         │  - OpenAIAdapter             │                   │
│         └──────────────┬───────────────┘                   │
│                        │                                    │
│         ┌──────────────▼───────────────┐                   │
│         │      rx.Model (Unified)      │                   │
│         │  - Message                   │                   │
│         │  - Conversation              │                   │
│         │  - ChatFolder                │                   │
│         └──────────────┬───────────────┘                   │
│                        │                                    │
│         ┌──────────────▼───────────────┐                   │
│         │    SQLite Database           │                   │
│         └──────────────────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         External: Anthropic API, OpenAI API
```

### 1.2 Architectural Principles

1. **Vertical Slice Architecture**: Features are organized by business capability, not technical layer
2. **Clean Architecture**: Business logic depends on interfaces, not concrete implementations
3. **Unified Model**: `rx.Model` eliminates duplication (DB + Domain + UI in one class)
4. **Dependency Inversion**: Use cases depend on `ILLMService`, not `AnthropicAdapter`
5. **Single Responsibility**: Each vertical slice owns its complete feature stack

---

## 2. Vertical Slices (Bounded Contexts)

### 2.1 Chat Feature (`features/chat/`)

**Responsibility**: Core chat conversation functionality with AI assistant

**Structure**:
```
features/chat/
├── models.py       # Message, Conversation (rx.Model - unified!)
├── use_cases.py    # SendMessageUseCase, LoadHistoryUseCase (pure logic)
├── state.py        # ChatState (rx.State - controller)
└── ui.py           # chat_area(), message_bubble(), chat_input() (components)
```

**Data Flow**:
1. User types message in UI → `chat_input()` component
2. Component calls `ChatState.handle_send_message()` (async background task)
3. State saves user message to DB via `rx.session()`
4. State calls `SendMessageUseCase.execute()`
5. Use case streams from `ILLMService` (AnthropicAdapter or OpenAIAdapter)
6. State appends chunks to AI message, saves final response to DB
7. UI auto-updates via Reflex reactivity

**Public Interface**:
- `ChatState.handle_send_message()`: Async method (user action)
- `ChatState.messages`: List[Message] (reactive state variable)
- `ChatState.is_generating`: bool (UI loading indicator)

### 2.2 Workspace Feature (`features/workspace/`)

**Responsibility**: Sidebar navigation, folder organization, chat management

**Structure**:
```
features/workspace/
├── models.py       # ChatFolder (rx.Model)
├── use_cases.py    # CreateFolderUseCase, MoveChatUseCase (if needed)
├── state.py        # WorkspaceState (rx.State)
└── ui.py           # sidebar(), folder_section(), chat_item()
```

**Public Interface**:
- `WorkspaceState.folders`: List[ChatFolder]
- `WorkspaceState.select_chat(chat_id)`: Navigate to chat
- `WorkspaceState.create_new_folder(name)`: Create folder

---

## 3. Core Infrastructure (`core/`)

### 3.1 LLM Ports (`core/llm_ports.py`)

**Purpose**: Interface-based LLM adapter pattern (Clean Architecture)

**Components**:
```python
# Domain Entities
class Role(str, Enum): USER, ASSISTANT, SYSTEM
class LLMConfig(BaseModel): temperature, enable_reasoning, reasoning_budget

# Interface (Port)
class ILLMService(ABC):
    async def generate_stream(prompt: str, config: LLMConfig) -> AsyncGenerator[str, None]

# Adapters (Implementations)
class AnthropicAdapter(ILLMService): ...
class OpenAIAdapter(ILLMService): ...
```

**Why This Matters**:
- ✅ Use cases depend on `ILLMService`, not concrete adapters
- ✅ Easy to swap providers (Anthropic ↔ OpenAI)
- ✅ Testable with `FakeLLMAdapter`
- ✅ Clean Architecture preserved in Reflex monolith

### 3.2 Database (`core/database.py`)

**Purpose**: Documentation and utilities for Reflex database usage

**Key Concepts**:
- `rx.Model`: Unified model (DB table + domain entity + UI state)
- `rx.session()`: Database session context manager
- **Critical Rule**: NEVER hold `rx.session()` during async LLM streaming

---

## 4. Data Models (Unified Approach)

### 4.1 Unified Model Philosophy

**Problem Solved**: The "Triple Model Tax"
- ❌ OLD: SQLAlchemy ORM Model → Pydantic Domain Entity → UI State Model (3 classes!)
- ✅ NEW: `rx.Model` (1 class serves all 3 purposes!)

**Benefits**:
- No mapping/serialization needed
- Single source of truth
- Reflex handles reactivity automatically
- Less boilerplate code

### 4.2 Message Model

**File**: `features/chat/models.py`

```python
import reflex as rx
from datetime import datetime
from typing import Optional

class Message(rx.Model, table=True):
    """
    Unified Message model.
    Simultaneously serves as:
    1. Database table (SQLAlchemy ORM)
    2. Domain entity (business logic)
    3. UI state variable (reactive)
    """
    # Primary key
    id: str

    # Foreign key
    conversation_id: str

    # Core fields
    role: str  # "user" | "assistant" | "system"
    content: str
    created_at: datetime = datetime.utcnow()

    # Optional metadata
    model_used: Optional[str] = None
    avatar_url: Optional[str] = None

    # UI computed property
    @property
    def is_user(self) -> bool:
        return self.role == "user"

    @property
    def timestamp_formatted(self) -> str:
        return self.created_at.strftime("%I:%M %p %d %b %Y")
```

**Database Table**: `messages`
**Domain Usage**: `message.role`, `message.is_user`
**UI Usage**: `rx.foreach(ChatState.messages, message_bubble)`

### 4.3 Conversation Model

**File**: `features/chat/models.py`

```python
class Conversation(rx.Model, table=True):
    """Chat conversation (aggregate root)"""
    id: str
    title: str = "New Chat"
    folder_id: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
```

**Relationships**: One Conversation has many Messages (via `conversation_id` FK)

### 4.4 ChatFolder Model

**File**: `features/workspace/models.py`

```python
class ChatFolder(rx.Model, table=True):
    """Folder for organizing conversations"""
    id: str
    name: str
    created_at: datetime = datetime.utcnow()
```

---

## 5. State Management (Controllers)

### 5.1 ChatState Pattern

**File**: `features/chat/state.py`

**Responsibilities**:
1. UI state management (input_text, is_generating)
2. Database session management (rx.session() safety)
3. Use case orchestration (calls SendMessageUseCase)
4. WebSocket updates to frontend (via `async with self`)

**Critical Pattern**:
```python
class ChatState(rx.State):
    # UI state
    messages: list[Message] = []
    input_text: str = ""
    is_generating: bool = False

    # Backend-only (not sent to browser)
    _llm_service: ILLMService = AnthropicAdapter(api_key=os.getenv("ANTHROPIC_API_KEY"))

    @rx.background
    async def handle_send_message(self):
        """
        CRITICAL REFLEX PATTERN:
        1. @rx.background decorator for async operations
        2. async with self: for state mutations
        3. Short-lived rx.session() calls
        """
        prompt = self.input_text

        # Step 1: Save user message (open session, write, close)
        async with self:
            self.input_text = ""
            self.is_generating = True

            user_msg = Message(conversation_id=self.current_chat_id, role="user", content=prompt)

            with rx.session() as session:
                session.add(user_msg)
                session.commit()

            self.messages.append(user_msg)
            self.messages = self.messages  # Trigger reactivity!

        # Step 2: Stream LLM (NO database session held!)
        use_case = SendMessageUseCase(self._llm_service)
        full_response = ""

        async for chunk in use_case.execute(self.current_chat_id, prompt):
            full_response += chunk
            # Update UI in real-time (optional)

        # Step 3: Save AI message (open NEW session, write, close)
        async with self:
            ai_msg = Message(conversation_id=self.current_chat_id, role="assistant", content=full_response)

            with rx.session() as session:
                session.add(ai_msg)
                session.commit()

            self.messages.append(ai_msg)
            self.messages = self.messages  # Trigger reactivity!
            self.is_generating = False
```

**Reflex Rules Enforced**:
- ✅ `@rx.background` for async LLM calls
- ✅ `async with self:` for state mutations
- ✅ `self.messages = self.messages` for reactivity
- ✅ Short-lived `rx.session()` (NEVER held during streaming)
