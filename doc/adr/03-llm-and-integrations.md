# 03 — LLM and Integrations

> **Cross-references**
> - Port: `mychat_reflex/core/llm_ports.py` — `ILLMService`, `LLMConfig(temperature, enable_reasoning, reasoning_budget)`, `Role`.
> - Adapters: `mychat_reflex/infrastructure/llm_adapters.py` — `AnthropicAdapter`, `OpenAIAdapter` (lazy SDK imports).
> - DI wiring: `mychat_reflex/mychat_reflex.py:initialize_dependencies()` + runtime swap in `ChatState._ensure_correct_adapter()`.
> - Architecture: [`doc/2-architecture/reflex-monolith-architecture.md`](../2-architecture/reflex-monolith-architecture.md) §4–10.
> - Tests: `tests/infrastructure/test_llm_adapters.py`, `tests/integration/test_anthropic_integration.py`.
> - Sibling ADRs: [`01-core-architecture.md`](01-core-architecture.md) · [`02-data-and-domain.md`](02-data-and-domain.md) · [`04-presentation-and-api.md`](04-presentation-and-api.md) · [`05-testing-and-qa.md`](05-testing-and-qa.md)

---

## ADR 003: Dependency Inversion for External AI Services
**Status:** Accepted

### Context
We must protect our core business logic from the volatility of external AI providers (OpenAI, Anthropic, Gemini).

### Decision
While we compromised on the Data Model (ADR 005-V2), we will **strictly enforce Clean Architecture for external services**. The Use Cases will only depend on an `ILLMService` interface. External SDKs will be wrapped in Adapter classes located in a shared `infrastructure/` layer.

### Consequences
*   **Positive:** We can swap AI providers or add local models (Ollama) without touching the Use Cases or the UI.
*   **Positive:** Enables blazing-fast, zero-cost unit/integration testing by injecting Fake adapters instead of hitting real APIs.
*   **Negative:** Requires defining and maintaining interface contracts.

### Related
- Interface: `ILLMService.generate_stream(prompt, config) -> AsyncGenerator[str, None]` in `core/llm_ports.py`.
- Use case dependency: `SendMessageUseCase(llm_service: ILLMService)` — never imports adapters directly.
- Reinforces ADR 012 (Hexagonal). Wiring is governed by ADR 015.

---

## ADR 007: Custom LLM Adapters over Third-Party Abstractions
**Status:** Accepted

### Context
The application must support multiple LLM providers (OpenAI, Anthropic, Gemini) and handle advanced, provider-specific features such as multimodal attachments (images/PDFs) and reasoning/thinking budgets. We evaluated using third-party abstraction libraries (LiteLLM, LangChain) versus building Custom Adapters implementing our own `ILLMService` interface.

### Decision
We will build **Custom Adapters** implementing our `ILLMService` interface. The Domain will define generic configurations (`LLMConfig`), and each Adapter will translate these into the provider's specific JSON schema.

### Consequences
*   **Positive:** We can adopt day-one features immediately.
*   **Negative:** Increased maintenance burden to write JSON mapping logic for new providers.

### Related
- Today: `AnthropicAdapter` and `OpenAIAdapter` in `mychat_reflex/infrastructure/llm_adapters.py`.
- Adapter selection at runtime: `ChatState._ensure_correct_adapter(model)` — routes by model name prefix (`claude*/sonnet*/opus*` → Anthropic, `gpt*/o1*/o3*` → OpenAI).
- Future providers (Gemini, Ollama) plug in by implementing `ILLMService` and being registered in `AppContainer`.

---

## ADR 008: Normalization of Advanced Reasoning Edge Cases
**Status:** Accepted

### Context
Different LLM providers implement reasoning differently, creating severe edge cases:
1. Anthropic: Requires a `thinking` block and strictly requires `temperature=1.0`.
2. OpenAI (o1/o3): Uses `reasoning_effort` and strictly forbids the `temperature` parameter.

### Decision
The Domain exposes a generic `LLMConfig(enable_reasoning: bool)`. The Adapters absorb the edge cases (e.g., the `AnthropicAdapter` force-overrides temperature to 1.0; the `OpenAIAdapter` strips the temperature parameter entirely).

### Consequences
*   **Positive:** The Use Case simply requests reasoning, and the Adapter ensures the API call doesn't crash with a 400 Bad Request.

### Related
- Generic config: `LLMConfig(temperature, enable_reasoning, reasoning_budget)` in `core/llm_ports.py`.
- UI surface: `thinking_selector()` and `temperature_selector()` popovers in `features/chat/ui.py`; values stored in LocalStorage as strings (see ADR 014 + `doc/guides/reflex-localstorage-best-practices.md`).
- Edge-case absorption lives in each adapter's `generate_stream` body — not in `ChatState` or use cases.

---

## ADR 010: System Prompt Resolution Strategy
**Status:** Accepted

### Context
The "System Prompt" is handled inconsistently:
1. OpenAI (gpt-4o): Uses `{"role": "system"}`.
2. OpenAI (o1): Forbids `system`, requires `developer` or `user`.
3. Anthropic: Forbids `system` in the array, requires a top-level `system=` kwarg.

### Decision
The Domain will exclusively use `Role.SYSTEM`. The Adapters will be responsible for "System Prompt Resolution" (e.g., AnthropicAdapter extracts it from the array and moves it to the top-level kwarg).

### Consequences
*   **Positive:** The `RAGPromptBuilder` can safely generate `Role.SYSTEM` messages without worrying about which model the user selected.

### Related
- `Role` enum: `mychat_reflex/core/llm_ports.py`.
- **Status note**: today `SendMessageUseCase` builds a flat string transcript ("User: … / Assistant: …") rather than a structured message array — system-prompt resolution per adapter is therefore not yet exercised. When structured messages are introduced (e.g., for multimodal per ADR 009), this ADR becomes load-bearing.
- Related: ADR 008 (reasoning normalisation) for the analogous "adapter absorbs the edge case" pattern.
