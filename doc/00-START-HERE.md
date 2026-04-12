<!--
LLM INSTRUCTION BLOCK
MOTIVATION: This is the Level 0 (30-second) onboarding document. It establishes the "Ubiquitous Language" and strict architectural boundaries for the entire project.
CONTENTS: Executive summary, domain dictionary, and the exact repository structure.
DO'S:
- DO strictly enforce the vocabulary defined here across all code, variables, and other documentation.
- DO respect the Vertical Slice Architecture. Code for a feature belongs in `src/features/[feature_name]/`, not in global horizontal folders.
- DO read `docs/execution-plan.md` before writing any code.
DON'TS:
- DO NOT invent synonyms in the codebase (e.g., if this file says "Message", do not use "ChatBubble" in the code).
- DO NOT create horizontal layers at the root of `src/` (e.g., no `src/models/` or `src/controllers/`).
-->

# 🚀 Project Overview & Domain Dictionary

## 1. Executive Summary
A commercial-grade, ChatGPT-like application built as a **Reflex full-stack monolith** featuring AI chat with LLM streaming, folder-based chat organization, and notes. It uses **Vertical Slice Architecture** to organize features as self-contained bounded contexts. The architecture employs a **Unified Model** approach where `rx.Model` serves as database table, domain entity, and UI state simultaneously, eliminating the "Triple Model Tax."

**Key Architecture Decision:** Migrated from dual-backend (Reflex + FastAPI) to Reflex monolith to eliminate HTTP/SSE overhead and state duplication while preserving Clean Architecture principles through interface-based LLM adapters.

## 2. Ubiquitous Language (The Dictionary)

### Core Domain Entities
*   **Message**: A single turn in a conversation. Unified `rx.Model` that is simultaneously: database row, domain entity, and UI state variable. Has `role` (user/assistant/system), `content`, `conversation_id`, timestamps.
*   **Conversation**: Represents a single chat session. Contains messages and belongs to optional folder. Unified `rx.Model`.
*   **ChatFolder**: Organizational container for grouping conversations. Unified `rx.Model`.

### Architecture Patterns
*   **Vertical Slice**: A self-contained feature with its own models, use cases, state, and UI (e.g., `features/chat/`).
*   **Bounded Context**: Domain-Driven Design term for a vertical slice with clear boundaries and its own ubiquitous language.
*   **Unified Model**: An `rx.Model` class that serves three purposes: 1) Database table (ORM), 2) Domain entity (business logic), 3) UI state variable (reactivity). This eliminates the "Triple Model Tax."

### Services & Interfaces
*   **ILLMService**: Abstract interface for LLM providers (Anthropic, OpenAI). Use cases depend on this, not concrete implementations.
*   **SendMessageUseCase**: Pure business logic for orchestrating message sending and LLM streaming. Remains testable.
*   **rx.State**: Reflex controller/ViewModel that handles UI events, database sessions, and use case orchestration.

### Reflex-Specific Terms
*   **rx.Model**: SQLAlchemy-based ORM model provided by Reflex. Automatically creates database tables.
*   **rx.State**: Reactive state container that syncs with frontend via WebSockets. Replaces traditional API controllers.
*   **rx.session()**: Database session context manager. MUST be short-lived (never held during async LLM calls).
*   **@rx.background**: Decorator for async methods that may block (e.g., LLM streaming). Prevents UI freezing.
*   **async with self**: Required pattern inside @rx.background to safely mutate state and trigger UI updates.

## 3. Strict Repository Structure
The codebase strictly follows **Vertical Slice (Screaming) Architecture**. Do not deviate from this tree.

```text
/
├── doc/                            ← Project Documentation
│   ├── 00-START-HERE.md            ← You are here (Ubiquitous Language)
│   ├── execution-plan.md           ← Active sprint tracker & task board
│   ├── refactor.md                 ← Migration strategy (dual-backend → monolith)
│   ├── /1-product-specs/           ← Feature requirements (The "What")
│   ├── /2-architecture/            ← Component contracts (The "How")
│   ├── /3-contracts/               ← DB schemas & data flows (The "Truth")
│   └── /adr/                       ← Architecture Decision Records
│
├── mychat_reflex/                  ← REFLEX MONOLITH (Source Code)
│   │
│   ├── mychat_reflex.py            ← Main entry point (app definition)
│   │
│   ├── core/                       ← Shared Infrastructure
│   │   ├── __init__.py
│   │   ├── database.py             ← Reflex DB config, rx.session() docs
│   │   └── llm_ports.py            ← ILLMService, AnthropicAdapter, OpenAIAdapter
│   │
│   └── features/                   ← THE VERTICAL SLICES (Screaming Architecture)
│       │
│       ├── chat/                   ← Bounded Context: Chat Conversations
│       │   ├── __init__.py
│       │   ├── models.py           ← rx.Model: Message, Conversation
│       │   ├── use_cases.py        ← SendMessageUseCase, LoadHistoryUseCase
│       │   ├── state.py            ← ChatState (rx.State controller)
│       │   └── ui.py               ← chat_area(), message_bubble(), chat_input()
│       │
│       └── workspace/              ← Bounded Context: Sidebar & Folders
│           ├── __init__.py
│           ├── models.py           ← rx.Model: ChatFolder
│           ├── use_cases.py        ← CreateFolderUseCase, MoveChatUseCase
│           ├── state.py            ← WorkspaceState
│           └── ui.py               ← sidebar(), folder_section()
│
├── tests/                          ← Integration Testing
│   ├── __init__.py
│   └── integration/                ← Reflex testing + Fake LLM adapters
│
├── assets/                         ← Static files (CSS, favicon)
├── rxconfig.py                     ← Reflex configuration
└── pyproject.toml                  ← Dependencies (Reflex, Anthropic, OpenAI)
```

**Key Architectural Rules:**

1. **Vertical Slice Isolation**: Each feature in `features/` is self-contained. Do NOT create horizontal layers at root.
2. **Screaming Architecture**: Folder names SCREAM their domain purpose (`chat/`, `workspace/`), not technical role.
3. **Unified Models**: `rx.Model` classes in `models.py` are DB tables, domain entities, AND UI state.
4. **Controlled Cross-Feature Imports**: Features may import `models.py` from other features to establish Foreign Keys (Shared Data Layer). However, a feature may NEVER import `state.py` or `ui.py` from another feature.
5. **Use Cases Stay Pure**: Business logic in `use_cases.py` depends on interfaces (`ILLMService`), not concrete adapters.
6. **State as Controller**: `state.py` files contain `rx.State` classes that orchestrate use cases and handle `rx.session()`.

7. The Database Session Rule**: `rx.session()` MUST be short-lived. Never hold a database session open while `await`-ing an LLM stream. Open session -> Save User Message -> Close Session -> Stream LLM -> Open Session -> Save AI Message -> Close Session.
## 4. High-Level System Context

### Technology Stack
*   **Framework:** Reflex (Python full-stack framework, compiles to React)
*   **Architecture:** Full-stack monolith (no separate backend API)
*   **Database:** SQLite via Reflex's rx.Model (SQLAlchemy under the hood)
*   **LLM Providers:** Anthropic Claude / OpenAI GPT (via `ILLMService` interface)
*   **State Management:** Reflex reactive state (WebSocket sync with frontend)
*   **Streaming:** Native Reflex async streaming (no SSE, no HTTP)

### Migration Status
🚧 **Currently migrating from:**
- ❌ Dual-backend: Reflex frontend + FastAPI backend + HTTP/SSE
- ❌ Triple Model Tax: ORM models + Domain entities + UI state models

✅ **To Reflex monolith:**
- ✅ Single codebase: All logic in `mychat_reflex/`
- ✅ Unified models: `rx.Model` serves all 3 purposes
- ✅ Direct function calls: No HTTP overhead
- ✅ Clean architecture preserved: Interface-based LLM adapters

### Development Workflow
1. **Read** `doc/00-START-HERE.md` (ubiquitous language)
2. **Check** `doc/execution-plan.md` (current sprint tasks)
3. **Follow** Vertical Slice pattern (group by feature, not layer)
4. **Test** with Reflex testing utilities + Fake LLM adapters
5. **Commit** atomic changes (one feature/fix per commit)
