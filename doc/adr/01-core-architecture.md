## ADR 001: Vertical Slice Architecture (Screaming Architecture)
**Status:** Accepted

### Context
The application needs to support distinct but interconnected features: Chat, RAG (Retrieval-Augmented Generation), and a Knowledge Base (Notes/Highlights). Traditional layered architectures (grouping all controllers together, all models together) make it difficult to locate feature-specific logic and often lead to tight coupling between unrelated domains.

### Decision
We will use **Vertical Slice Architecture**. The directory structure will "scream" the business features (`features/chat/`, `features/knowledge_base/`). Inside each feature, code is divided into `models.py` (Unified Data), `use_cases.py` (Business Logic), `state.py` (Reflex Controller), and `ui.py` (Reflex Components).

### Consequences
*   **Positive:** High cohesion. If the "Notes" feature changes, only the `knowledge_base` directory is touched.

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

---
