# Reflex Monolith Architecture Specification

**Document Status:** Active
**Last Updated:** 2026-05-04
**Architecture Pattern:** Vertical Slice (Screaming) Architecture + Clean Architecture (Hexagonal Ports & Adapters)

> This document describes the **as-built** architecture of the Reflex monolith.
> Authoritative cross-references:
> - Code: `mychat_reflex/`
> - ADRs: `doc/adr/01-core-architecture.md` … `doc/adr/05-testing-and-qa.md`
> - DB schema: `doc/3-reference/database-schema.md`
> - Reflex-specific guidance: `doc/rules/reflex.md`, `doc/guides/reflex-localstorage-best-practices.md`

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         REFLEX MONOLITH                              │
│                                                                      │
│   Browser ── WebSocket ── Reflex Runtime (state sync)                │
│                                   │                                  │
│                                   ▼                                  │
│   ┌──────────────────────────────────────────────────────────┐       │
│   │                     PRESENTATION                         │       │
│   │   pages/main.py  ──  features/*/ui.py  ──  ui/primitives │       │
│   └──────────────────────────────────────────────────────────┘       │
│                                   │                                  │
│                                   ▼                                  │
│   ┌──────────────────────────────────────────────────────────┐       │
│   │                  STATE (rx.State controllers)            │       │
│   │    ChatState                       KnowledgeBaseState    │       │
│   └──────────────────────────────────────────────────────────┘       │
│                │                                                     │
│                ▼                                                     │
│   ┌──────────────────────────────────────────────────────────┐       │
│   │             USE CASES (pure business logic)              │       │
│   │     SendMessageUseCase            LoadHistoryUseCase     │       │
│   └──────────────────────────────────────────────────────────┘       │
│                │                          │                          │
│                ▼ depends on               ▼ depends on               │
│   ┌─────────────────────────┐   ┌─────────────────────────────┐      │
│   │   CORE (ports + DI)     │   │  rx.Model (unified)         │      │
│   │   ILLMService           │   │  Message, Conversation,     │      │
│   │   LLMConfig, Role       │   │  ChatFolder                 │      │
│   │   AppContainer (DI)     │   └─────────────────────────────┘      │
│   └─────────────────────────┘                │                       │
│                ▲                              ▼                      │
│                │ implements           SQLite (Alembic-managed)       │
│   ┌─────────────────────────────────────────────────┐                │
│   │            INFRASTRUCTURE (adapters)            │                │
│   │   AnthropicAdapter        OpenAIAdapter         │                │
│   └─────────────────────────────────────────────────┘                │
│                │                                                     │
└────────────────┼─────────────────────────────────────────────────────┘
                 ▼
       External APIs: Anthropic, OpenAI
```

### 1.2 Architectural Principles

1. **Vertical Slice Architecture** — features are organised by business capability (`features/chat/`, `features/knowledge_base/`, `features/workspace/`), not by technical layer.
2. **Clean Architecture / Hexagonal** — use cases depend on the `ILLMService` *port* (in `core/`); concrete *adapters* live in `infrastructure/`. The dependency arrow always points inward.
3. **Unified Model** — `rx.Model` plays three roles at once: DB table, domain entity, UI state value (eliminates the "Triple Model Tax").
4. **Dependency Injection via Service Locator** — `AppContainer` (in `core/di.py`) is wired once at the Composition Root (`mychat_reflex.py`) — see ADR 015.
5. **Single source of business logic** — `ChatState` is a *controller/ViewModel* that delegates to use cases; it never embeds prompt construction or LLM calls.

---

## 2. Project Layout (as-built)

```
mychat_reflex/
├── mychat_reflex.py            # Composition Root: app, logging, DI wiring
├── pages/
│   └── main.py                 # main_page() — composes sidebar + chat + notes
├── core/                       # Pure, no framework, no third-party SDKs
│   ├── llm_ports.py            # ILLMService (port), LLMConfig, Role
│   ├── di.py                   # AppContainer service locator
│   └── database.py             # rx.session() docs + DatabaseConfig helper
├── infrastructure/             # Concrete adapters (third-party SDKs live HERE)
│   └── llm_adapters.py         # AnthropicAdapter, OpenAIAdapter
├── features/                   # Vertical slices
│   ├── chat/
│   │   ├── models.py           # Message, Conversation, ChatFolder (rx.Model)
│   │   ├── use_cases.py        # SendMessageUseCase, LoadHistoryUseCase
│   │   ├── state.py            # ChatState (rx.State controller)
│   │   └── ui.py               # chat_area, message_bubble, chat_input, …
│   ├── knowledge_base/
│   │   ├── state.py            # KnowledgeBaseState (notes panel)
│   │   └── ui.py               # notes_panel, notes_header, notes_content
│   └── workspace/
│       └── ui.py               # sidebar(), folder_section, chat_item, …
└── ui/
    └── primitives.py           # Cross-cutting components: pill_btn, icon_btn,
                                # nav_item, footer_btn, card, divider,
                                # text_input, popover

alembic/                        # DB migrations (Alembic, not Reflex CLI)
└── versions/da92f255a8fe_.py   # Baseline: chatfolder, conversation, message
```

> **Note**: `features/workspace/` deliberately has **no `state.py` and no `models.py`** today. Sidebar UI binds directly to `ChatState` (folders, chats, sidebar_search) and `ChatFolder` lives in `features/chat/models.py`. Splitting workspace into its own state/models is tracked as future work — see §15.

---

## 3. Vertical Slices

### 3.1 Chat Feature (`features/chat/`)

**Responsibility**: Core chat conversation with an AI assistant — message persistence, streaming, history, model/temperature/reasoning controls, markdown + code rendering.

**Files**:
```
features/chat/
├── models.py       # Message, Conversation, ChatFolder
├── use_cases.py    # SendMessageUseCase, LoadHistoryUseCase (pure)
├── state.py        # ChatState (rx.State)
└── ui.py           # chat_area + many helper components
```

**Data Flow** (send message):
1. User types in `chat_input()` → `ChatState.set_input_text` updates `input_text`.
2. User clicks Send / presses Enter → `ChatState.handle_send_message()` (background event handler) is invoked.
3. State persists the user message via short-lived `rx.session()`, appends it to `self.messages`, and creates an empty assistant placeholder.
4. State resolves `ILLMService` from `AppContainer` and calls `SendMessageUseCase.execute(conversation_id, user_message, history, config)`.
5. The use case builds a transcript from `history`, calls `llm.generate_stream(...)`, and yields chunks.
6. State buffers chunks (40-char windows), calls `_close_open_code_block()` to keep partial Markdown valid, then mutates `self.messages[-1].content` inside `async with self:` to push WebSocket frames.
7. When the stream ends, state opens a fresh `rx.session()` to persist the final assistant message and bump `conversation.updated_at`.

**Public Interface**:
- `ChatState.handle_send_message()` — `@rx.event(background=True)` async handler.
- `ChatState.messages: list[Message]` — reactive UI state.
- `ChatState.is_generating: bool` — loading indicator.
- `ChatState.on_load()` — page-load hook; populates messages, folders, chats.

### 3.2 Workspace Feature (`features/workspace/`)

**Responsibility**: Sidebar layout — header, search, navigation list of folders/chats, footer.

**Files**:
```
features/workspace/
└── ui.py    # sidebar(), sidebar_header(), action_buttons(),
             # sidebar_search(), chat_item(), folder_section(),
             # navigation_list(), sidebar_footer()
```

**State binding**: All sidebar widgets bind to **`ChatState`** (no dedicated `WorkspaceState` exists yet):
- `ChatState.folders`, `ChatState.chats`, `ChatState.filtered_folders`
- `ChatState.sidebar_search` + `set_sidebar_search`
- `ChatState.create_new_chat`, `ChatState.create_new_folder`, `ChatState.select_chat`

### 3.3 Knowledge Base Feature (`features/knowledge_base/`)

**Responsibility**: Right-hand "notes" panel — a free-text scratchpad living next to the chat.

**Files**:
```
features/knowledge_base/
├── state.py    # KnowledgeBaseState
└── ui.py       # notes_panel(), notes_header(), notes_content()
```

**Public Interface**:
- `KnowledgeBaseState.notes_content: str`
- `KnowledgeBaseState.set_notes_content(value)`
- `KnowledgeBaseState.clear_notes()`

> The Knowledge Base slice is intentionally minimal today — it has no persistence, no models, no use cases. Its existence is documented here so the architecture diagram matches `pages/main.py`, which composes `sidebar() | chat_area() | notes_panel()`.

---

## 4. Core (`core/`)

`core/` is **pure**: no Reflex (except `core/database.py`, which is a thin docstring + helper around `rx.config`), no third-party SDKs, no I/O.

### 4.1 LLM Ports (`core/llm_ports.py`)

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncGenerator, Optional
from pydantic import BaseModel


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class LLMConfig(BaseModel):
    temperature: float = 0.7
    enable_reasoning: bool = False
    reasoning_budget: Optional[int] = None


class ILLMService(ABC):
    @abstractmethod
    async def generate_stream(
        self, prompt: str, config: Optional[LLMConfig] = None
    ) -> AsyncGenerator[str, None]:
        ...
```

**Why this matters**:
- Use cases depend on `ILLMService`, never on `AnthropicAdapter` / `OpenAIAdapter`.
- Swapping providers (or fakes) is a one-line change at the Composition Root.
- Tests use `FakeLLMAdapter` (see `tests/features/chat/test_use_cases.py`).

### 4.2 Dependency Injection (`core/di.py`) — ADR 015

A minimal **Service Locator**:

```python
class AppContainer:
    _llm_service: Optional[ILLMService] = None

    @classmethod
    def register_llm_service(cls, service: ILLMService): ...
    @classmethod
    def resolve_llm_service(cls) -> ILLMService: ...
    @classmethod
    def clear(cls): ...   # for tests
```

**Rules**:
- `core/di.py` **must not** import from `infrastructure/`.
- Wiring lives in `mychat_reflex.py:initialize_dependencies()`.
- Tests that need a fake adapter call `AppContainer.register_llm_service(FakeLLMAdapter(...))` and `AppContainer.clear()` in teardown.

### 4.3 Database Helper (`core/database.py`)

Documentation module + a `DatabaseConfig.get_db_url()` shim. The actual engine and session factory are configured by Reflex from `rxconfig.py`. Use `rx.session()` for all DB access.

**Critical rule** (also enforced in `state.py`): **NEVER** hold `rx.session()` open across an `await`, especially across LLM streaming.

---

## 5. Infrastructure (`infrastructure/`)

### 5.1 LLM Adapters (`infrastructure/llm_adapters.py`)

```python
class AnthropicAdapter(ILLMService):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        from anthropic import AsyncAnthropic   # lazy import
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate_stream(self, prompt, config=None) -> AsyncGenerator[str, None]:
        ...   # honours config.temperature, config.enable_reasoning, config.reasoning_budget


class OpenAIAdapter(ILLMService):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        from openai import AsyncOpenAI         # lazy import
        ...
```

**Why lazy imports?** So the app starts even if only one provider's SDK is installed (e.g., a slim Anthropic-only deployment doesn't need `openai`).

**`config.enable_reasoning` / `config.reasoning_budget`**: Anthropic's "extended thinking" mode. When enabled, the adapter includes reasoning parameters in the API call and the user-facing UI gates this with the `thinking_selector()` popover and the reasoning-budget popover.

---

## 6. Data Models (Unified Approach)

### 6.1 Why Unified

| Old (3 classes) | New (`rx.Model`) |
|---|---|
| ORM model + Pydantic domain entity + UI VM | One class |
| Manual mapping/serialisation | Reflex handles it |
| Drift between layers | Single source of truth |

### 6.2 `Message`

`features/chat/models.py`:

```python
class Message(rx.Model, table=True):
    id: str = Field(primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id")
    role: str                            # "user" | "assistant" | "system"
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_used: Optional[str] = None
    avatar_url: Optional[str] = None

    @property
    def is_user(self) -> bool:       return self.role == "user"
    @property
    def is_assistant(self) -> bool:  return self.role == "assistant"
    @property
    def timestamp_formatted(self) -> str:
        return self.created_at.strftime("%I:%M %p %d %b %Y")
```

> **`default_factory` is intentional**. `created_at: datetime = datetime.utcnow()` would be evaluated **once at class-definition time**, making every row share the same timestamp.

### 6.3 `Conversation`

```python
class Conversation(rx.Model, table=True):
    id: str = Field(primary_key=True)
    title: str = "New Chat"
    folder_id: Optional[str] = Field(default=None, foreign_key="chatfolder.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_in_folder(self) -> bool:
        return self.folder_id is not None
```

### 6.4 `ChatFolder`

```python
class ChatFolder(rx.Model, table=True):
    id: str = Field(primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

> `ChatFolder` lives in `features/chat/models.py` today, even though semantically it belongs to the workspace slice. See §15.

For full SQL schema, FK behaviour, and index recommendations, see `doc/3-reference/database-schema.md`.

---

## 7. State Management (`features/chat/state.py`)

### 7.1 Responsibilities of `ChatState`

1. **UI state** — `messages`, `input_text`, `is_generating`, `current_conversation_id`, `current_chat_title`, `folders`, `chats`, `sidebar_search`.
2. **User preferences** in `rx.LocalStorage` — `selected_model`, `temperature`, `enable_reasoning`, `reasoning_budget`, `code_theme`, `light_code_theme`. **All stored as strings** to avoid hydration type-mismatch crashes (see `doc/guides/reflex-localstorage-best-practices.md`); typed access goes through computed vars (`temperature_float`, `enable_reasoning_bool`, `reasoning_budget_int`).
3. **DB session lifetime** — open `rx.session()` only briefly, never across `await`.
4. **Use-case orchestration** — call `LoadHistoryUseCase` / `SendMessageUseCase`, never call the LLM directly.
5. **Adapter switching** — `_ensure_correct_adapter(model)` re-registers an Anthropic or OpenAI adapter in `AppContainer` when the user changes models.

### 7.2 The Send-Message Pattern (as-implemented)

```python
class ChatState(rx.State):
    messages: list[Message] = []
    input_text: str = ""
    is_generating: bool = False
    current_conversation_id: str = "default-chat"

    selected_model: str = rx.LocalStorage("claude-sonnet-4-5")  # always string
    # … other LocalStorage prefs …

    @rx.event(background=True)
    async def handle_send_message(self):
        # ── guard ──────────────────────────────────────────────
        async with self:
            prompt = self.input_text
            if not prompt.strip() or self.is_generating:
                return

        # ── 1. persist user message + clear input ──────────────
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
            self.messages = self.messages   # nudge reactivity

        # ── 2. assistant placeholder ───────────────────────────
        ai_msg_id = str(uuid4())
        async with self:
            self.messages.append(Message(
                id=ai_msg_id,
                conversation_id=self.current_conversation_id,
                role="assistant",
                content="",
            ))
            self.messages = self.messages

        # ── 3. resolve LLM, build config, stream ───────────────
        await self._ensure_correct_adapter(self.selected_model)
        llm = AppContainer.resolve_llm_service()
        use_case = SendMessageUseCase(llm)

        chat_history = self.messages[:-2]   # exclude user_msg + placeholder
        full_response = ""

        async for chunk in use_case.execute(
            conversation_id=self.current_conversation_id,
            user_message=prompt,
            history=chat_history,
            config=LLMConfig(
                temperature=self.temperature_float,
                enable_reasoning=self.enable_reasoning_bool,
                reasoning_budget=self.reasoning_budget_int,
            ),
        ):
            # 40-char buffer → fewer WebSocket frames, smoother UI
            char_buffer = ""
            for ch in chunk:
                char_buffer += ch
                full_response += ch
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

        # ── 4. persist final assistant message ─────────────────
        async with self:
            with rx.session() as session:
                session.add(Message(
                    id=ai_msg_id,
                    conversation_id=self.current_conversation_id,
                    role="assistant",
                    content=full_response,
                ))
                conv = session.get(Conversation, self.current_conversation_id)
                if conv:
                    conv.updated_at = datetime.now(timezone.utc)
                session.commit()
            self.messages[-1].content = full_response   # drop the safety ```
            self.is_generating = False
            self.messages = self.messages
```

**Reflex rules enforced** (cross-ref ADR 002-V2 and `doc/rules/reflex.md`):
- `@rx.event(background=True)` — async + non-blocking. (`@rx.background` is the legacy alias; the codebase uses the modern decorator.)
- `async with self:` for **every** state mutation.
- `self.messages = self.messages` to nudge reactivity after in-place list mutation.
- `rx.session()` opened in short, awaitless blocks.
- Chunk buffering (40 chars + `asyncio.sleep(0.01)`) to keep React from thrashing.
- `_close_open_code_block()` keeps mid-stream Markdown valid (prevents `react-markdown` from misparsing `# comments` in unclosed fences as headings).

### 7.3 Key Helpers

- `_close_open_code_block(content: str) -> str` — appends a closing ```` ``` ```` to mid-stream content if the count of fences is odd.
- `_ensure_correct_adapter(model)` — chooses `AnthropicAdapter` for `claude*/sonnet*/opus*` or `OpenAIAdapter` for `gpt*/o1*/o3*`, builds it with the right env API key, and re-registers in `AppContainer`.

---

## 8. Use Case Layer

### 8.1 `SendMessageUseCase` (Command)

`features/chat/use_cases.py`:

```python
class SendMessageUseCase:
    def __init__(self, llm_service: ILLMService):
        self.llm = llm_service

    async def execute(
        self,
        conversation_id: str,
        user_message: str,
        history: List[Message],
        config: Optional[LLMConfig] = None,
    ) -> AsyncGenerator[str, None]:
        config = config or LLMConfig(temperature=0.7)

        # Build a transcript so the model has memory of the conversation.
        transcript = ""
        for msg in history:
            speaker = "User" if msg.is_user else "Assistant"
            transcript += f"{speaker}: {msg.content}\n\n"
        transcript += f"User: {user_message}\n\nAssistant:"

        async for chunk in self.llm.generate_stream(prompt=transcript, config=config):
            yield chunk
```

**What this use case does NOT do** (intentionally — those belong to `ChatState`):
- No DB access.
- No `rx.session()`.
- No UI state mutation.
- No adapter selection.

**Testability**: `tests/features/chat/test_use_cases.py` injects a `FakeLLMAdapter` and asserts on streamed chunks — no Reflex runtime, no DB.

### 8.2 `LoadHistoryUseCase` (Query)

```python
class LoadHistoryUseCase:
    async def execute(self, session: Session, conversation_id: str) -> List[Message]:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(session.exec(statement).all())
```

**Notes**:
- The `session` is **passed in** (not created). Lifetime is the caller's concern. ADR 014.
- Uses modern SQLModel `select()` — not `session.query(...)`.
- `ChatState.on_load` and `ChatState.select_chat` open a short `rx.session()` and call this use case.

---

## 9. UI Layer

### 9.1 Composition

`pages/main.py:main_page()` composes the three vertical slices side-by-side:

```python
def main_page() -> rx.Component:
    return rx.hstack(
        sidebar(),       # features/workspace/ui.py
        chat_area(),     # features/chat/ui.py
        notes_panel(),   # features/knowledge_base/ui.py
        spacing="0",
        height="100vh",
    )
```

### 9.2 Shared Primitives (`mychat_reflex/ui/primitives.py`)

A cross-cutting component library used by every slice:

| Primitive | Purpose |
|---|---|
| `pill_btn(*children)` | Rounded pill-style button (model selector, etc.) |
| `icon_btn(icon, on_click, extra)` | Round icon button |
| `icon_btn_square(icon, on_click, extra)` | Square icon button |
| `nav_item(*children)` | Sidebar list row |
| `footer_btn(*children)` | Sidebar footer button |
| `card(*children)` | Generic surface |
| `divider(axis)` | Horizontal/vertical rule |
| `text_input(placeholder, value, on_change, extra)` | Styled `rx.input` |
| `popover(trigger, content, min_width)` | Popover wrapper |

**Rule**: presentation that is reused across slices belongs in `ui/primitives.py`. Components that are slice-specific (`message_bubble`, `chat_input`, `model_selector`, `notes_panel`, …) stay in their slice's `ui.py`.

### 9.3 Chat UI Highlights (`features/chat/ui.py`)

- `chat_area()` — header + history + input
- `chat_header()` + `global_search()`
- `chat_history()` — `rx.foreach(ChatState.messages, message_bubble)`
- `message_bubble(message, index)` — user/assistant styling, avatar, timestamp, `message_actions`
- `_message_markdown(content, is_streaming)` — Markdown renderer with Shiki code blocks (`ShikiHighLevelCodeBlock`); falls back to a fast renderer while streaming
- `chat_input()` — input field + `_input_left()` / `_input_right()` (model/thinking/temperature popovers + send)
- `model_selector()`, `thinking_selector()`, `temperature_selector()` — popover-based settings backed by `ChatState` LocalStorage prefs
- `_close_open_code_block` is called in `state.py`, not the UI, so the renderer always sees balanced fences

---

## 10. Composition Root (`mychat_reflex/mychat_reflex.py`)

This is the **only** module allowed to wire concrete adapters into `core/`:

```python
import os, logging
import reflex as rx
from dotenv import load_dotenv

from .pages.main import main_page
from .core.di import AppContainer
from .infrastructure.llm_adapters import AnthropicAdapter

def initialize_dependencies():
    load_dotenv()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key    = os.getenv("OPENAI_API_KEY", "")
    if anthropic_key:
        AppContainer.register_llm_service(
            AnthropicAdapter(api_key=anthropic_key, model="claude-sonnet-4-5")
        )
    elif openai_key:
        from .infrastructure.llm_adapters import OpenAIAdapter
        AppContainer.register_llm_service(
            OpenAIAdapter(api_key=openai_key, model="gpt-4o")
        )
    else:
        logging.error("No API keys found! Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env")

initialize_dependencies()

def index() -> rx.Component:
    return main_page()

app = rx.App(theme=rx.theme(appearance="inherit", has_background=False,
                            radius="large", accent_color="indigo"),
             stylesheets=["/styles.css"])
app.add_page(index, title="Super Chat 2")
```

**Key points**:
- API keys come from `.env` (loaded explicitly with `python-dotenv`).
- The chosen adapter is the **default**. At runtime `_ensure_correct_adapter` may swap it when the user picks a different model.

---

## 11. Error Handling

The current `handle_send_message` does **not** wrap the streaming loop in `try/except`. A failure mid-stream surfaces as a Reflex runtime error. Hardening this is a known gap (§15). The intended pattern when implemented:

```python
@rx.event(background=True)
async def handle_send_message(self):
    try:
        ...   # current happy-path body
    except Exception as e:
        async with self:
            self.messages[-1].content = f"❌ Error: {e}"
            self.messages = self.messages
            self.is_generating = False
        # optionally persist as a system message for the audit log
```

---

## 12. Testing Strategy (as-built)

Test layout in repo:

```
tests/
├── core/
│   └── test_di.py                       # AppContainer behaviour
├── features/
│   └── chat/
│       ├── test_models.py               # Message/Conversation properties
│       └── test_use_cases.py            # SendMessageUseCase + LoadHistoryUseCase
│                                        # (uses FakeLLMAdapter + in-memory SQLite)
├── infrastructure/
│   └── test_llm_adapters.py             # AnthropicAdapter / OpenAIAdapter (mocked SDKs)
├── integration/
│   └── test_anthropic_integration.py    # opt-in real-API smoke test
└── test_send_message_use_case.py        # ⚠ orphan duplicate; consolidate (§15)
```

**Conventions**:
- Use cases are tested with `FakeLLMAdapter` and an in-memory SQLite engine — no Reflex runtime, no network.
- Adapters are tested with mocked SDK clients.
- `tests/core/test_di.py` covers `register / resolve / clear` + the "uninitialized → RuntimeError" path.
- See ADR 05 (`doc/adr/05-testing-and-qa.md`) and `doc/rules/tdd-tester.md` for conventions.

---

## 13. Performance Considerations

### 13.1 Streaming
The 40-char buffer + 10 ms sleep in `handle_send_message` is empirically tuned to balance perceived latency vs. WebSocket / React thrash. Lower it for snappier streaming on fast clients; raise it for slow networks.

### 13.2 DB Queries
- Today: one `select(Message)` per conversation load — fine for the typical < 200-message chat.
- Future: paginate (see `database-schema.md` §9.2) once a conversation exceeds a few hundred messages.
- Add the recommended composite index `(conversation_id, created_at)` before that becomes a hot path.

### 13.3 Memory
- `ChatState.messages` holds the full conversation in memory.
- For very long chats: load tail + lazy-load older pages on scroll-up (not implemented).

---

## 14. Security

### 14.1 API Keys
- Loaded from `.env` at the Composition Root.
- Stored only on `AnthropicAdapter.client` / `OpenAIAdapter.client` (instance-scoped).
- **Never** placed on `rx.State` attributes — those serialise to the browser. If a state field must hold a secret-adjacent value, prefix it with `_` (Reflex treats underscore-prefixed attrs as backend-only).

### 14.2 Input Validation
The send guard rejects empty / whitespace-only prompts and re-entrancy while `is_generating`. Length limits, content moderation, and rate limiting are not implemented.

### 14.3 SQL Injection
SQLModel parameterises all comparisons. Don't build raw SQL strings around user input.

---

## 15. Known Drift / Future Work

| Item | Current state | Owner / next step |
|---|---|---|
| `WorkspaceState` | Doesn't exist; sidebar binds to `ChatState` | Extract folder/chat list state from `ChatState` |
| `features/workspace/models.py` | Doesn't exist; `ChatFolder` lives in `features/chat/models.py` | Move when `WorkspaceState` is extracted |
| Error handling in `handle_send_message` | No try/except around stream | Wrap; persist error as system message |
| `ChatFolder` deletion semantics | No FK ON DELETE rules | Migration to add `SET NULL` / `CASCADE` |
| Indexes | Only PK/FK | Migration adding `(conversation_id, created_at)` etc. |
| `tests/test_send_message_use_case.py` | Orphan duplicate of `tests/features/chat/test_use_cases.py` with redundant imports | Delete; keep the one under `tests/features/chat/` |
| Knowledge Base persistence | In-memory only | Add `Note` model + use cases when product-spec is written |
| Keyboard shortcuts | Send-on-Enter only | Shift+Enter newline, Esc to cancel stream |
| Conversation rename / delete | Not implemented in `ChatState` | Add `rename_chat`, `delete_chat` event handlers |
| Markdown rendering | Implemented (Shiki) | Already done — keep specs in sync |

---

## 16. Cross-references

- **ADRs** — `doc/adr/`
  - 01 Core architecture (vertical slices, hex)
  - 02 Data and domain (rx.Model, sessions, ADR 002-V2 streaming pattern)
  - 03 LLM and integrations (ports/adapters, ADR 015 DI)
  - 04 Presentation and API (Reflex-only, no FastAPI)
  - 05 Testing and QA
- **Rules** — `doc/rules/`
  - `reflex.md`, `reflex-gui.md`, `reflex_shiki_rules.md`, `tdd-tester.md`, `rules.md`
- **Guides** — `doc/guides/reflex-localstorage-best-practices.md` (string-only LocalStorage + computed-var converters)
- **Schema** — `doc/3-reference/database-schema.md`
- **Product spec** — `doc/1-product-specs/chat-feature-spec.md`
