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
