## 🏗️ 1. Core Architectural Principles
This project strictly adheres to **Screaming Architecture**, **Clean Architecture (Hexagonal)**, and **Command Query Separation (CQS)**.
*   **Screaming Architecture:** Code is grouped by business feature (`features/chat`, `features/knowledge_base`), not by technical layer.
*   **Clean Core:** The `core/` and `use_cases.py` files MUST NOT import `reflex`, `anthropic`, `openai`, or any infrastructure SDKs. They are pure Python.
*   **CQS:**
    *   *Commands* (mutate state) and *Queries* (read state) are strictly separated in `use_cases.py`.
    *   UI Event Handlers (`handle_click`) are Commands. Computed Vars (`@rx.var`) are Queries.
*   **Dependency Inversion:** Use Cases depend on Interfaces (`ILLMService`). Concrete implementations (`AnthropicAdapter`) live in `infrastructure/` and are injected via `AppContainer` at startup.

## ⚛️ 2. Reflex UI & AST Compilation Rules (CRITICAL)
Reflex UI functions are executed *once* at compile time to generate a React AST. They do not run in the browser.
*   **NO Python Control Flow in UI:** Never use standard `if/else` or `for` loops in UI components. You MUST use `rx.cond`, `rx.match`, and `rx.foreach`.
*   **NO String Manipulation on Vars:** Never call `.split()`, `.upper()`, or `.replace()` on an `rx.Var` (e.g., `message.content.split()`). It will crash the compiler. Use Reflex components like `rx.markdown()` to handle text formatting.
*   **Dumb Components:** UI functions (`ui.py`) must be pure functions that only return `rx.Component`. All logic belongs in `state.py`.

## 🧠 3. Reflex State & WebSocket Management
Reflex synchronizes state between the backend and the React frontend via WebSockets.
*   **Async Background Tasks:** Any LLM call or long-running task MUST be decorated with `@rx.event(background=True)`.
*   **State Mutation:** Inside a background task, you MUST use `async with self:` to mutate state.
*   **WebSocket Buffering:** When streaming LLM text, DO NOT `yield` on every single character. This floods the WebSocket and freezes the browser. Accumulate tokens and `yield` every ~5 chunks (e.g., `if chunk_count % 5 == 0: yield`).
*   **Backend-Only State:** Any variable in `rx.State` that should NOT be sent to the browser (like API clients or raw embeddings) MUST be prefixed with an underscore (e.g., `_llm_service`).

## 💾 4. Database & SQLModel Rules
We use `rx.Model` (SQLModel/SQLAlchemy) for unified database and UI models.
*   **Modern Syntax:** Use `session.exec(select(Model))` instead of the deprecated `session.query(Model)`.
*   **Short-Lived Sessions:** Open `rx.session()`, read/write, and close it immediately. NEVER hold a database session open during an LLM stream.
*   **Prevent DetachedInstanceError:** When loading database objects into the UI state, you MUST clone them into pure in-memory objects to detach them from the SQLAlchemy session.
    *   *Example:* `self.messages = [Message(**m.model_dump()) for m in db_messages]`
*   **No Lambdas in Models:** Never use `lambda` in a `Field(default_factory=...)`. It breaks Reflex's Pydantic serialization. Pass a named function reference instead.

## 🧪 5. Testing Philosophy
We test the business logic, not the framework.
*   **The "Do Not Test" Zone:** Do not write `pytest` unit tests for `ui.py`, `state.py`, or `main.py`. These will be tested later via Playwright E2E tests.
*   **Use-Case Testing:** Test `use_cases.py` using an in-memory SQLite database and a `FakeLLMAdapter`. These tests must run in `< 0.05` seconds.
*   **Mocking Async Generators:** `unittest.mock` is notoriously broken when dealing with async generators (like OpenAI's stream). Do not use `AsyncMock` for this. Instead, build a pure Python **Fake** class that yields a fake chunk and stores `last_kwargs` for assertions.
*   **Mocking Async Context Managers:** For SDKs like Anthropic that use `async with`, use `unittest.mock.patch` and explicitly mock the `__aenter__` method to return the fake stream.
