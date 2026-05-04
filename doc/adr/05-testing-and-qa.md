# 05 — Testing and QA

> **Cross-references**
> - Test layout:
>   - `tests/core/test_di.py` — `AppContainer` (ADR 015).
>   - `tests/features/chat/test_models.py` — `Message` / `Conversation` properties.
>   - `tests/features/chat/test_use_cases.py` — **canonical** use-case integration tests with `FakeLLMAdapter` + in-memory SQLite.
>   - `tests/infrastructure/test_llm_adapters.py` — adapters with mocked SDK clients.
>   - `tests/integration/test_anthropic_integration.py` — opt-in real-API smoke test.
> - Architecture: [`doc/2-architecture/reflex-monolith-architecture.md`](../2-architecture/reflex-monolith-architecture.md) §12.
> - Conventions: [`doc/rules/tdd-tester.md`](../rules/tdd-tester.md), [`doc/rules/rules.md`](../rules/rules.md).
> - Sibling ADRs: [`01-core-architecture.md`](01-core-architecture.md) · [`02-data-and-domain.md`](02-data-and-domain.md) · [`03-llm-and-integrations.md`](03-llm-and-integrations.md) · [`04-presentation-and-api.md`](04-presentation-and-api.md)

---

## ADR 006-V2: Use-Case Driven Integration Testing
**Status:** Accepted (Replaces ADR 006)

### Context
Testing a chat application with a GUI (via Playwright/Selenium) is slow and brittle. Previously, we planned to use FastAPI's `TestClient` for API-level tests. However, per ADR 011, we dropped FastAPI to use Reflex as a Full-Stack Monolith. Reflex hides its internal FastAPI instance, meaning HTTP-based integration tests are no longer viable for our core logic.

### Decision
We will prioritize **Use-Case Driven Integration Tests**. Because we strictly adhere to Clean Architecture (ADR 012), our Use Cases are pure Python classes. Our test suite will directly instantiate these Use Cases, injecting an in-memory SQLite database and a `FakeLLMAdapter`.

### Consequences
*   **Positive:** Tests run in milliseconds, not minutes.
*   **Positive:** Zero cost for running the test suite on every commit (no real LLM API calls).
*   **Positive:** Tests are completely decoupled from the Reflex framework.
*   **Negative:** Does not test frontend React/Reflex rendering logic or WebSocket serialization.

### Related
- Canonical example: `tests/features/chat/test_use_cases.py` — instantiates `SendMessageUseCase` with a `FakeLLMAdapter`, instantiates `LoadHistoryUseCase` with an in-memory `Session`, asserts streamed chunks and DB state. Pattern is the test-suite blueprint.
- The fake adapter (`FakeLLMAdapter`) implements `ILLMService` directly — no Reflex runtime, no network. Possible because of ADR 003 + ADR 012.
- DI for tests: `AppContainer.register_llm_service(FakeLLMAdapter(...))` + `AppContainer.clear()` in teardown (see `tests/core/test_di.py`).
- Adapter contract tests use mocked `AsyncAnthropic` / `AsyncOpenAI` — see `tests/infrastructure/test_llm_adapters.py`.
- Real-API smoke test (`tests/integration/test_anthropic_integration.py`) is opt-in and requires `ANTHROPIC_API_KEY`; it is not part of the default `pytest` run.
- **Cleanup note (2026-05-04)**: the orphan `tests/test_send_message_use_case.py` (a duplicate of the canonical file with redundant repeated imports) has been deleted to avoid confusion.
