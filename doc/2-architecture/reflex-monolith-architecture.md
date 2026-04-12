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

---

## 6. Use Case Layer (Pure Business Logic)

### 6.1 SendMessageUseCase

**File**: `features/chat/use_cases.py`

**Responsibility**: Orchestrate message sending and LLM streaming

**Key Principle**: Remains PURE - no database, no state management, only business logic

```python
from typing import AsyncGenerator
from mychat_reflex.core.llm_ports import ILLMService, LLMConfig

class SendMessageUseCase:
    """
    Pure business logic for sending messages.

    This use case depends on ILLMService interface (Clean Architecture).
    It does NOT handle:
    - Database persistence (State's responsibility)
    - UI updates (State's responsibility)
    - rx.session() management (State's responsibility)

    It ONLY handles:
    - Streaming from LLM
    - Business logic around message generation
    """

    def __init__(self, llm_service: ILLMService):
        """
        Inject LLM service dependency.

        Args:
            llm_service: Implementation of ILLMService (AnthropicAdapter, OpenAIAdapter, or FakeLLM)
        """
        self.llm = llm_service

    async def execute(
        self,
        conversation_id: str,
        user_message: str,
        config: LLMConfig | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream AI response for user message.

        Args:
            conversation_id: The conversation context
            user_message: User's input text
            config: Optional LLM configuration (temperature, reasoning, etc.)

        Yields:
            Text chunks from the LLM as they arrive

        Note: This method is PURE - it has no side effects.
        The caller (ChatState) is responsible for:
        1. Saving user message to DB before calling this
        2. Saving AI response to DB after streaming completes
        """
        config = config or LLMConfig(temperature=0.7)

        # Business logic: You could add prompt engineering here
        # For example: add conversation history, RAG context, etc.
        # For MVP, we just pass the user message directly

        # Stream from LLM service
        async for chunk in self.llm.generate_stream(prompt=user_message, config=config):
            yield chunk

        # Future: Add business logic here (e.g., post-processing, content filtering)
```

**Testing**:
```python
# tests/integration/test_send_message_use_case.py
from mychat_reflex.core.llm_ports import ILLMService, LLMConfig
from mychat_reflex.features.chat.use_cases import SendMessageUseCase
from typing import AsyncGenerator

class FakeLLMService(ILLMService):
    """Fake LLM for testing"""
    async def generate_stream(self, prompt: str, config: LLMConfig | None = None) -> AsyncGenerator[str, None]:
        # Simulate streaming
        for word in ["Hello", " ", "world", "!"]:
            yield word

async def test_send_message_use_case():
    # Arrange
    fake_llm = FakeLLMService()
    use_case = SendMessageUseCase(fake_llm)

    # Act
    chunks = []
    async for chunk in use_case.execute("conv-1", "Test prompt"):
        chunks.append(chunk)

    # Assert
    assert "".join(chunks) == "Hello world!"
```

### 6.2 LoadHistoryUseCase

**File**: `features/chat/use_cases.py`

```python
import reflex as rx
from typing import List
from mychat_reflex.features.chat.models import Message

class LoadHistoryUseCase:
    """
    Load conversation message history.

    This could be pure, but since it's a simple query,
    we'll use rx.session() directly for MVP.
    """

    def execute(self, conversation_id: str) -> List[Message]:
        """
        Load all messages for a conversation.

        Args:
            conversation_id: The conversation to load

        Returns:
            List of messages ordered by created_at
        """
        with rx.session() as session:
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at).all()

            # Important: Detach from session before returning
            session.expunge_all()
            return messages
```

---

## 7. UI Component Layer

### 7.1 Component Structure

**File**: `features/chat/ui.py`

```python
import reflex as rx
from .state import ChatState
from .models import Message

def message_bubble(message: Message) -> rx.Component:
    """
    Render a single message bubble.

    Args:
        message: Message model instance

    Returns:
        Reflex component for message display
    """
    is_user = message.role == "user"

    return rx.box(
        rx.hstack(
            # Avatar
            rx.avatar(
                src=message.avatar_url if is_user else "/ai-avatar.png",
                size="sm"
            ),
            # Message content
            rx.vstack(
                rx.text(
                    message.content,
                    class_name="message-text",
                ),
                rx.text(
                    message.timestamp_formatted,
                    class_name="message-timestamp",
                    size="sm",
                    color="gray"
                ),
                align_items="start" if not is_user else "end",
            ),
            spacing="3",
            justify="end" if is_user else "start",
            width="100%",
        ),
        class_name="message-bubble-user" if is_user else "message-bubble-ai",
    )


def chat_history() -> rx.Component:
    """
    Render scrollable list of messages.

    Uses rx.foreach to iterate over ChatState.messages
    with automatic reactivity.
    """
    return rx.box(
        rx.foreach(
            ChatState.messages,
            message_bubble,
        ),
        class_name="chat-history",
        overflow_y="auto",
        flex="1",
    )


def chat_input() -> rx.Component:
    """
    Message input area with send button.
    """
    return rx.hstack(
        # Text input
        rx.input(
            placeholder="Type a message...",
            value=ChatState.input_text,
            on_change=ChatState.set_input_text,
            on_key_down=lambda key: ChatState.handle_send_message() if key == "Enter" else None,
            disabled=ChatState.is_generating,
            flex="1",
        ),
        # Send button
        rx.button(
            "Send",
            on_click=ChatState.handle_send_message,
            disabled=ChatState.is_generating,
        ),
        spacing="3",
        class_name="chat-input",
    )


def chat_area() -> rx.Component:
    """
    Main chat area - combines all chat components.
    """
    return rx.vstack(
        # Header (future: add chat title, actions)
        rx.heading(ChatState.current_chat_title, size="lg"),

        # Message history
        chat_history(),

        # Input area
        chat_input(),

        class_name="chat-area",
        height="100vh",
        spacing="4",
    )
```

---

## 8. Integration Patterns

### 8.1 Dependency Injection Pattern

**Problem**: How do we inject `ILLMService` into use cases?

**Solution**: Create instances in State initialization

```python
# features/chat/state.py
import os
from mychat_reflex.core.llm_ports import AnthropicAdapter, OpenAIAdapter, ILLMService

class ChatState(rx.State):
    # ... state variables ...

    def __init__(self):
        super().__init__()

        # Dependency injection: Choose LLM provider based on config
        provider = os.getenv("LLM_PROVIDER", "anthropic")

        if provider == "anthropic":
            self._llm_service = AnthropicAdapter(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
            )
        elif provider == "openai":
            self._llm_service = OpenAIAdapter(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o")
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
```

### 8.2 Error Handling Pattern

```python
@rx.background
async def handle_send_message(self):
    try:
        # ... normal flow ...
        async for chunk in use_case.execute(...):
            full_response += chunk
    except Exception as e:
        # Handle errors gracefully
        async with self:
            error_msg = Message(
                conversation_id=self.current_chat_id,
                role="assistant",
                content=f"❌ Error: {str(e)}"
            )
            self.messages.append(error_msg)
            self.messages = self.messages
            self.is_generating = False
```

### 8.3 Real-time Streaming Pattern

**Option 1: Batch chunks for UI updates**
```python
async for chunk in use_case.execute(...):
    full_response += chunk

    # Update UI every 5 chunks to reduce WebSocket overhead
    if len(full_response) % 5 == 0:
        async with self:
            # Update the last message in the list
            self.messages[-1].content = full_response
            self.messages = self.messages
```

**Option 2: Update on complete only (simpler for MVP)**
```python
async for chunk in use_case.execute(...):
    full_response += chunk

# Update UI once at the end
async with self:
    ai_msg = Message(...)
    self.messages.append(ai_msg)
    self.messages = self.messages
```

---

## 9. Testing Strategy

### 9.1 Unit Tests (Use Cases)

**File**: `tests/unit/test_send_message_use_case.py`

```python
import pytest
from mychat_reflex.features.chat.use_cases import SendMessageUseCase
from tests.fakes import FakeLLMService

@pytest.mark.asyncio
async def test_send_message_streams_from_llm():
    # Arrange
    fake_llm = FakeLLMService(response="Hello world!")
    use_case = SendMessageUseCase(fake_llm)

    # Act
    chunks = []
    async for chunk in use_case.execute("conv-1", "Test"):
        chunks.append(chunk)

    # Assert
    assert "".join(chunks) == "Hello world!"
    assert fake_llm.was_called_with(prompt="Test")
```

### 9.2 Integration Tests (State + Use Cases)

**File**: `tests/integration/test_chat_feature.py`

```python
import pytest
import reflex as rx
from mychat_reflex.features.chat.chat_state import ChatState
from mychat_reflex.features.chat.models import Message
from tests.fakes import FakeLLMService


@pytest.mark.asyncio
async def test_send_message_integration():
    # Arrange: Setup state with fake LLM
    state = ChatState()
    state._llm_service = FakeLLMService(response="Test AI response")

    # Act: Send message
    state.input_text = "Hello AI"
    await state.handle_send_message()

    # Assert: Check database persistence
    with rx.session() as session:
        messages = session.query(Message).filter(
            Message.conversation_id == state.current_chat_id
        ).all()

        assert len(messages) == 2  # User + AI
        assert messages[0].role == "user"
        assert messages[0].content == "Hello AI"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Test AI response"
```

### 9.3 UI Component Tests

**File**: `tests/ui/test_chat_components.py`

```python
from mychat_reflex.features.chat.ui import message_bubble
from mychat_reflex.features.chat.models import Message
from datetime import datetime

def test_message_bubble_renders_user_message():
    # Arrange
    msg = Message(
        id="msg-1",
        conversation_id="conv-1",
        role="user",
        content="Test message",
        created_at=datetime.utcnow()
    )

    # Act
    component = message_bubble(msg)

    # Assert
    assert component is not None
    # Add more specific assertions based on Reflex testing utilities
```

---

## 10. Performance Considerations

### 10.1 Database Query Optimization

**Problem**: Loading 1000+ messages could be slow

**Solutions**:
1. **Pagination**: Load last 50 messages, lazy-load older ones
2. **Indexing**: Ensure `conversation_id` and `created_at` are indexed
3. **Caching**: Cache recent messages in State (avoid repeated queries)

```python
class ChatState(rx.State):
    _message_cache: dict[str, List[Message]] = {}

    def load_messages(self, conversation_id: str):
        # Check cache first
        if conversation_id in self._message_cache:
            self.messages = self._message_cache[conversation_id]
            return

        # Load from DB
        with rx.session() as session:
            messages = session.query(Message).filter(...).all()
            session.expunge_all()

            # Cache for future use
            self._message_cache[conversation_id] = messages
            self.messages = messages
```

### 10.2 Streaming Optimization

**Problem**: Too many WebSocket updates during streaming

**Solution**: Batch chunks before triggering reactivity

```python
CHUNK_BATCH_SIZE = 50  # characters

async for chunk in use_case.execute(...):
    full_response += chunk

    # Only update UI every N characters
    if len(full_response) % CHUNK_BATCH_SIZE == 0:
        async with self:
            self.messages[-1].content = full_response
            self.messages = self.messages
```

### 10.3 Memory Management

**Problem**: Long conversations consume memory

**Solution**: Implement message limit and archiving

```python
MAX_MESSAGES_IN_MEMORY = 500

class ChatState(rx.State):
    def load_messages(self, conversation_id: str):
        with rx.session() as session:
            # Load only recent messages
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(MAX_MESSAGES_IN_MEMORY).all()

            # Reverse to chronological order
            self.messages = list(reversed(messages))
```

---

## 11. Security Considerations

### 11.1 API Key Management

**Critical**: Never expose API keys to browser!

```python
class ChatState(rx.State):
    # ✅ CORRECT: Backend-only variable (starts with _)
    _llm_service: ILLMService = None

    # ❌ WRONG: Would be sent to browser!
    # api_key: str = os.getenv("ANTHROPIC_API_KEY")
```

### 11.2 Input Validation

```python
@rx.background
async def handle_send_message(self):
    prompt = self.input_text.strip()

    # Validate input
    if not prompt:
        return  # Don't send empty messages

    if len(prompt) > 10000:
        async with self:
            self.error_message = "Message too long (max 10000 characters)"
        return
```

### 11.3 Content Filtering (Future)

```python
def is_safe_content(text: str) -> bool:
    """Check for inappropriate content (placeholder)"""
    # Implement content filtering logic
    # Could use external service or regex patterns
    return True
```

---

## 12. Deployment Considerations

### 12.1 Environment Configuration

**File**: `.env` (never commit!)
```bash
# LLM Provider
LLM_PROVIDER=anthropic  # or "openai"

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Database
DATABASE_URL=sqlite:///reflex.db
```

### 12.2 Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied (`reflex db migrate`)
- [ ] API keys secured (use secrets manager)
- [ ] Error logging configured
- [ ] Performance monitoring (track LLM latency)
- [ ] Rate limiting on LLM calls (prevent abuse)
- [ ] HTTPS enabled (for production deployment)

---

## 13. Migration from Old Architecture

### 13.1 What's Being Removed

```
❌ src/                          # Entire FastAPI backend
❌ src/main.py                   # FastAPI app entry point
❌ src/features/chat/presentation/routes.py  # HTTP endpoints
❌ mychat_reflex/state/chat_state.py  # Old state with HTTP calls
❌ mychat_reflex/components/      # Old component structure
```

### 13.2 What's Being Kept

```
✅ Business Logic               # Use cases remain testable
✅ LLM Adapters                # Interface pattern preserved
✅ Database Schema             # Similar tables, different ORM
✅ UI Components               # Refactored to features/*/ui.py
```

### 13.3 Breaking Changes

1. **No HTTP API**: Frontend can't make fetch() calls anymore
2. **No SSE**: Use Reflex WebSocket streaming instead
3. **No Pydantic models**: Use rx.Model instead
4. **No FastAPI dependencies**: Install Reflex dependencies

---

## 14. Future Enhancements

### 14.1 RAG Integration (Post-MVP)

```python
# features/chat/use_cases.py
class SendMessageWithRAGUseCase:
    def __init__(
        self,
        llm_service: ILLMService,
        vector_store: IVectorStore  # New dependency
    ):
        self.llm = llm_service
        self.vector_store = vector_store

    async def execute(self, conversation_id: str, user_message: str):
        # 1. Search vector store
        context = await self.vector_store.search(user_message, limit=5)

        # 2. Build prompt with context
        enhanced_prompt = f"Context: {context}\n\nQuestion: {user_message}"

        # 3. Stream from LLM
        async for chunk in self.llm.generate_stream(enhanced_prompt):
            yield chunk
```

### 14.2 Conversation Branching

```python
class Message(rx.Model, table=True):
    id: str
    conversation_id: str
    parent_message_id: Optional[str] = None  # For branching
    # ... other fields ...
```

### 14.3 Multi-modal Support

```python
class Message(rx.Model, table=True):
    content: str  # JSON string with content parts
    content_type: str = "text"  # "text" | "multimodal"

    @property
    def parsed_content(self):
        if self.content_type == "multimodal":
            return json.loads(self.content)
        return self.content
```
