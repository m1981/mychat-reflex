# 01 — Core Architecture

> **Cross-references**
> - Architecture overview: [`doc/2-architecture/reflex-monolith-architecture.md`](../2-architecture/reflex-monolith-architecture.md) — implements ADRs 001, 011, 012, 015 in code.
> - Code: `mychat_reflex/features/` (slices), `mychat_reflex/core/` (ports + DI), `mychat_reflex/infrastructure/` (adapters), `mychat_reflex/mychat_reflex.py` (composition root).
> - Sibling ADRs: [`02-data-and-domain.md`](02-data-and-domain.md) · [`03-llm-and-integrations.md`](03-llm-and-integrations.md) · [`04-presentation-and-api.md`](04-presentation-and-api.md) · [`05-testing-and-qa.md`](05-testing-and-qa.md)

---

## ADR 001: Vertical Slice Architecture (Screaming Architecture)
**Status:** Accepted

### Context
The application needs to support distinct but interconnected features: Chat, RAG (Retrieval-Augmented Generation), and a Knowledge Base (Notes/Highlights). Traditional layered architectures (grouping all controllers together, all models together) make it difficult to locate feature-specific logic and often lead to tight coupling between unrelated domains.

### Decision
We will use **Vertical Slice Architecture**. The directory structure will "scream" the business features (`features/chat/`, `features/knowledge_base/`). Inside each feature, code is divided into `models.py` (Unified Data), `use_cases.py` (Business Logic), `state.py` (Reflex Controller), and `ui.py` (Reflex Components).

### Consequences
*   **Positive:** High cohesion. If the "Notes" feature changes, only the `knowledge_base` directory is touched.

### Related
- Implementation: `mychat_reflex/features/{chat,workspace,knowledge_base}/` — see architecture doc §2.
- Reinforced by ADR 011 (Reflex Monolith) and ADR 012 (Hexagonal).

***

## ADR 011: The "Screaming Reflex" Full-Stack Monolith (NEW)
**Status:** Accepted
**Date:** 2023-10-27

### Context
The application needs to handle distinct domains (Chat, Knowledge Base, RAG Search). We must decide how to deploy and scale these domains for a single-user/hobby scale (approx. 1,000 chats and 500MB of data). The previous decoupled FastAPI/Reflex design created a "Dual-Backend Chasm," introducing unnecessary network overhead for this scale.

### Decision
We will drop FastAPI entirely and use **Reflex as a Full-Stack Monolith**. The `src/features/` directory (Vertical Slices) will live directly inside the Reflex project. Reflex's `rx.State` will act as the Controller, directly instantiating and calling pure Python Use Cases.

### Consequences
*   **Positive:** Eliminates the HTTP/Network tax. Development speed is drastically increased.
*   **Positive:** We retain Vertical Slice Architecture (Screaming Architecture) while utilizing Reflex's native strengths.
*   **Negative:** The application is now tightly coupled to the Reflex framework. Extracting the backend to a mobile app later will require re-introducing an API layer.

### Related
- Implementation: `mychat_reflex/mychat_reflex.py` (composition root + `rx.App`), `mychat_reflex/pages/main.py`.
- See architecture doc §10 "Composition Root".
- Conflicts with hypothetical FastAPI/SSE design — explicitly retired by ADR 002-V2 and ADR 006-V2.

---

## ADR 012: Hexagonal Architecture (Ports and Adapters)
**Status:** Accepted

### Context
The application relies heavily on third-party infrastructure: Vector Databases (ChromaDB, Voyage AI) and LLM APIs (OpenAI, Anthropic, Gemini). Tying the core business logic directly to these external SDKs creates vendor lock-in, makes future migrations highly risky, and makes automated testing expensive and slow.

### Decision
We will adopt **Hexagonal Architecture** (also known as Ports and Adapters) for the internal code structure.
*   **The Core (Hexagon):** Contains pure Python Domain Entities and Use Cases.
*   **Ports:** The Core defines abstract Interfaces (e.g., `IVectorStore`, `ILLMService`).
*   **Adapters:** The Infrastructure layer implements these interfaces (e.g., `ChromaDBAdapter`, `OpenAIAdapter`).

### Consequences
*   **Positive:** Fulfills the strict requirement for a safe migration path from ChromaDB to Voyage AI.
*   **Positive:** Enables blazing-fast, cost-free integration testing by plugging `FakeAdapters` into the Ports during test runs.
*   **Positive:** Protects the core application from breaking changes in third-party SDKs.
*   **Negative:** Introduces boilerplate. Developers must write Interfaces and map data between Infrastructure models (SQLAlchemy) and Domain models (Pydantic/Dataclasses).

### Related
- Port: `mychat_reflex/core/llm_ports.py` (`ILLMService`, `LLMConfig`, `Role`).
- Adapters: `mychat_reflex/infrastructure/llm_adapters.py` (`AnthropicAdapter`, `OpenAIAdapter`).
- Boilerplate is partially mitigated by ADR 005-V2 (`rx.Model` unifies DB + domain + UI).
- DI mechanism: ADR 015.

---
## ADR 015: Dependency Injection via Service Locator in Reflex State (NEW)
**Status:** Accepted

### Context
Hexagonal Architecture (ADR 012) requires Dependency Injection (DI) so that Use Cases receive their Adapters (e.g., `ChromaDBAdapter`) from the outside. However, Reflex instantiates `rx.State` classes automatically under the hood. We cannot easily pass dependencies into the `__init__` method of a Reflex State. If we hardcode `use_case = SendMessageUseCase(OpenAIAdapter())` inside the State, we violate our architecture and make testing impossible.

### Decision
We will implement a lightweight **Service Locator / DI Container** pattern. A central registry (e.g., `AppContainer`) will be configured at application startup. Reflex `rx.State` classes will resolve their required Use Cases from this container during event handlers.

### Consequences
*   **Positive:** Preserves Hexagonal Architecture. The Reflex State remains decoupled from concrete Infrastructure adapters.
*   **Positive:** Allows us to easily swap out the `AppContainer` configuration during testing to inject Fakes.
*   **Negative:** Service Locator is sometimes considered an anti-pattern compared to pure constructor injection, but it is a necessary pragmatic compromise when working with framework-managed lifecycles like `rx.State`.

### Related
- Container: `mychat_reflex/core/di.py` (`AppContainer.register_llm_service` / `resolve_llm_service` / `clear`).
- Wiring: `mychat_reflex/mychat_reflex.py:initialize_dependencies()`.
- Runtime swapping: `ChatState._ensure_correct_adapter()` re-registers an adapter when the user changes model family.
- Tested in: `tests/core/test_di.py`.
- See architecture doc §4.2 and §10.

***
