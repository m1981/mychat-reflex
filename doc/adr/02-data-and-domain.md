## ADR 004: Command Query Separation (CQS) over Full CQRS
**Status:** Accepted

### Context
The application needs to search across 1,000 chats and ~500MB of artifacts. Full CQRS (Command Query Responsibility Segregation) would dictate separate databases for reading (e.g., Elasticsearch) and writing (e.g., Postgres), synchronized via an event bus.

### Decision
Given the scale (single-user hobby project, 500MB data), full CQRS is rejected due to extreme over-engineering. Instead, we will use **Command Query Separation (CQS)** at the code level. Use Cases will be strictly divided into Commands (e.g., `SendMessageUseCase` which mutates state) and Queries (e.g., `SearchNotesUseCase` which only reads state). Both will interact with the same SQLite database.

### Consequences
*   **Positive:** Eliminates the infrastructure cost and eventual-consistency bugs of an event bus.
*   **Positive:** SQLite FTS5 or standard SQLAlchemy queries are more than fast enough for 500MB of data.
*   **Negative:** If the app scales to millions of users, the single SQLite database will become a bottleneck (acceptable tradeoff for current scope).

---

## ADR 005-V2: Unified Models via `rx.Model` (SQLModel)
**Status:** Accepted (Replaces ADR 005)

### Context
Strict Clean Architecture demands that Domain models know nothing about the Database to prevent `LazyInitializationError`s when async loops access un-hydrated relationships. However, enforcing this strict separation in a Python/Reflex AI app requires writing triple the state-management code (DB Model -> Domain Model -> UI Model).

### Decision
We will adopt a **Pragmatic Compromise**. We will use Reflex's `rx.Model` (which is SQLModel/Pydantic under the hood) as our unified data structure. A single `Message` class will serve as the Database Table, the Domain Entity passed to Use Cases, and the UI State rendered by React.

### Consequences
*   **Positive:** Eliminates the "Boilerplate Tax." Adding a new column (e.g., `is_pinned`) requires changing exactly one line of code.
*   **Positive:** LLM Agents can easily understand the data flow without getting lost in mapping functions.
*   **Negative:** The Domain layer is technically "polluted" by the Reflex framework (`rx.Model`).

## ADR 009: Polymorphic Message Content for Multimodal Edge Cases
**Status:** Accepted

### Context
Users need to upload images and documents.
*   OpenAI expects images as a URL or base64 string inside an `image_url` object.
*   Anthropic expects base64 data inside a `source` object and strictly requires the `media_type` (e.g., `image/jpeg`).
*   Gemini expects an `inline_data` object.

### Decision
We will define polymorphic domain entities: `TextPart`, `ImagePart`, and `DocumentPart`. Because we are using `rx.Model` (SQLModel), this polymorphic list will be serialized into a JSON column in the SQLite database, but treated as a List of Pydantic objects in the application layer.

### Consequences
*   **Positive:** The frontend and Use Cases only deal with a standard `ImagePart(base64, mime_type)`.
*   **Negative:** Adapters become slightly more complex, requiring type-checking (`isinstance(part, ImagePart)`) during payload construction.
