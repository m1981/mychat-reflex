## ADR 001: Vertical Slice & Clean Architecture (Screaming Architecture)
**Status:** Accepted
**Date:** 2023-10-26

### Context
The application needs to support distinct but interconnected features: Chat, RAG (Retrieval-Augmented Generation), and a Knowledge Base (Notes/Highlights). Traditional layered architectures (grouping all controllers together, all models together) make it difficult to locate feature-specific logic and often lead to tight coupling between unrelated domains.

### Decision
We will use **Vertical Slice Architecture** at the root level, combined with **Clean Architecture** inside each slice. The directory structure will "scream" the business features (`chat/`, `knowledge_base/`, `rag_engine/`). Inside each feature, code will be strictly divided into `domain/`, `use_cases/`, `infrastructure/`, and `presentation/`.

### Consequences
*   **Positive:** High cohesion. If the "Notes" feature changes, only the `knowledge_base` directory is touched.
*   **Positive:** Easy to delete or extract features later.
*   **Negative:** Slight duplication of boilerplate (e.g., each feature might need its own router setup).

***

## ADR 011: Modular Monolith Deployment Architecture
**Status:** Accepted
**Date:** 2023-10-26

### Context
The application needs to handle distinct domains (Chat, Knowledge Base/Notes, RAG Search). We must decide how to deploy and scale these domains. The expected scale is a single-user hobby project with approximately 1,000 chats and 500MB of artifact data. 

### Decision
We will build and deploy the application as a **Modular Monolith**. 
*   **Monolith:** The entire application (all features, API endpoints, and background tasks) will run in a single process and be deployed to a single server.
*   **Modular:** Internally, the code will be strictly divided into isolated modules (Vertical Slices) that do not share database tables directly, communicating only through defined Use Cases.

### Consequences
*   **Positive:** Drastically simplifies deployment, CI/CD, and infrastructure costs compared to Microservices.
*   **Positive:** Eliminates network latency between the Chat engine and the Knowledge Base.
*   **Positive:** Easy to debug and trace errors since everything runs in one memory space.
*   **Negative:** If the application unexpectedly scales to millions of users, we cannot scale the "Search" feature independently of the "Chat" feature (an acceptable tradeoff for the current scope).

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

