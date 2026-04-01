## ADR 003: Dependency Inversion for External AI Services
**Status:** Accepted

### Context
The project currently uses ChromaDB and local/OpenAI models, but has a strict requirement to migrate to Voyage AI in the future. Tying the application logic directly to ChromaDB or OpenAI SDKs will require a massive rewrite during the migration.

### Decision
We will apply the **Dependency Inversion Principle (DIP)**. The core domain will define strict interfaces (`IVectorStore`, `ILLMService`). The application Use Cases will only depend on these interfaces. External SDKs (Chroma, Voyage, OpenAI) will be wrapped in Adapter classes located in the `infrastructure/` layer.

### Consequences
*   **Positive:** Migrating to Voyage AI requires writing exactly one new class (`VoyageAdapter`) and changing one line in the Dependency Injection container.
*   **Positive:** Enables blazing-fast unit/integration testing by injecting Fake adapters.
*   **Negative:** Requires defining and maintaining interface contracts.

---

## ADR 007: Custom LLM Adapters over Third-Party Abstractions
**Status:** Accepted
**Date:** 2023-10-26

### Context
The application must support multiple LLM providers (OpenAI, Anthropic, Gemini) and handle advanced, provider-specific features such as multimodal attachments (images/PDFs) and reasoning/thinking budgets. We evaluated using third-party abstraction libraries (LiteLLM, LangChain) versus building Custom Adapters implementing our own `ILLMService` interface.

### Decision
We will build **Custom Adapters** in the `infrastructure/llm/` layer. The Domain layer will define generic configurations (e.g., `LLMConfig`, `ImagePart`), and each Adapter will be strictly responsible for translating these generic concepts into the provider's specific JSON schema.

### Consequences
*   **Positive:** The core Use Cases remain 100% agnostic to provider API changes.
*   **Positive:** We can adopt day-one features (e.g., a new Claude "thinking" parameter) immediately without waiting for an open-source library to update.
*   **Negative:** Increased maintenance burden. We must manually write the JSON mapping logic for new providers.

---

## ADR 008: Normalization of Advanced Reasoning ("Thinking") Edge Cases
**Status:** Accepted

### Context
Different LLM providers implement "System 2" reasoning entirely differently, creating severe edge cases:
1.  **Anthropic (Claude 3.7):** Requires a `thinking` block with a `budget_tokens` integer. **Crucially, it strictly requires `temperature=1.0`** when thinking is enabled. If you pass `temperature=0.7`, the API throws a 400 error.
2.  **OpenAI (o1 / o3-mini):** Uses a `reasoning_effort` string (`"low"`, `"medium"`, `"high"`). **Crucially, it does not support the `temperature` parameter at all.** If you pass `temperature`, the API throws a 400 error.

### Decision
The Domain layer will expose a generic `LLMConfig(enable_reasoning: bool, reasoning_budget: int)`.
The Adapters will absorb the edge cases:
*   The `AnthropicAdapter` will intercept `enable_reasoning=True`, map the budget, and **force-override** the temperature to `1.0` before making the HTTP call.
*   The `OpenAIAdapter` will intercept `enable_reasoning=True`, map the integer budget to a `"high"/"medium"/"low"` string heuristic, and **strip** the `temperature` parameter from the payload entirely.

### Consequences
*   **Positive:** The `SendMessageUseCase` does not need `if provider == 'anthropic'` logic. It simply requests reasoning, and the Adapter ensures the API call doesn't crash.
*   **Positive:** Prevents 400 Bad Request errors caused by conflicting parameters.

---

## ADR 010: System Prompt Resolution Strategy
**Status:** Accepted

### Context
The concept of a "System Prompt" is handled inconsistently across the industry:
1.  **OpenAI (gpt-4o):** Accepts `{"role": "system", "content": "..."}` as the first message in the array.
2.  **OpenAI (o1-preview):** **Does not support the `system` role.** It requires system instructions to be passed as the `user` role, or in newer models, the `developer` role.
3.  **Anthropic:** Does not allow `system` in the messages array. It must be passed as a top-level parameter (`anthropic.messages.create(system="...", messages=[...])`).

### Decision
The Domain layer will continue to use `ChatMessage(role=Role.SYSTEM)`.
The Adapters will be responsible for "System Prompt Resolution":
*   `OpenAIAdapter` (for `gpt-4o`): Passes it through normally.
*   `OpenAIAdapter` (for `o1`): Intercepts the `SYSTEM` role and mutates it to `DEVELOPER` or prepends it to the first `USER` message.
*   `AnthropicAdapter`: Extracts all `SYSTEM` messages from the array, concatenates them, removes them from the message list, and passes them to the top-level `system=` kwarg.

### Consequences
*   **Positive:** The `RAGPromptBuilder` domain service can safely generate `Role.SYSTEM` messages without worrying about which model the user selected. The architecture remains pure.

Here are the Architecture Decision Records (ADRs) documenting the high-level structural patterns we just discussed. You can append these directly to your `adrs.md` file.