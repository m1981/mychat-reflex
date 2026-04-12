## ADR 006: API-First Integration Testing Strategy
**Status:** Accepted

### Context
Testing a chat application with a GUI (via Playwright/Selenium) is slow, brittle, and difficult to run in CI/CD pipelines. However, we need high confidence that the database, RAG retrieval, and LLM generation work together correctly.

### Decision
We will prioritize **API-level Integration Tests** using FastAPI's `TestClient`. We will use Dependency Injection overrides to swap the real LLM for a predictable `FakeLLMAdapter` during standard tests. To test the actual LLM/Voyage adapters, we will use the **VCR pattern** (recording and replaying HTTP traffic) to avoid recurring API costs.

### Consequences
*   **Positive:** Tests run in milliseconds, not minutes.
*   **Positive:** Zero cost for running the test suite on every commit.
*   **Negative:** Does not test frontend React/Reflex rendering logic (which will require separate, minimal UI tests if desired).


This is a highly mature architectural decision. By choosing **Custom Adapters** over a third-party abstraction like LiteLLM or LangChain, you are prioritizing **Domain Purity** and **Control**.

When dealing with cutting-edge AI features (like Anthropic's "Thinking" or OpenAI's `o3` reasoning), third-party libraries often lag behind or force you into "leaky abstractions" where provider-specific quirks infect your core business logic.

Here are the Architecture Decision Records (ADRs) documenting this choice, specifically addressing the **corner edge cases** your adapters will need to handle. You should append these to your `adrs.md` file.

***
