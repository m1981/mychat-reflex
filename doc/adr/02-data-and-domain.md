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

## ADR 005: Strict Separation of Domain Models and ORM Models
**Status:** Accepted

### Context
SQLAlchemy models are tied to database sessions. Passing SQLAlchemy objects directly into Use Cases or LLM Adapters can cause `LazyInitializationError`s if the async event loop tries to access a relationship after the database session has closed.

### Decision
We will maintain pure Python/Pydantic models in the `domain/` layer (e.g., `ChatMessage`) and SQLAlchemy models in the `infrastructure/` layer (e.g., `Message`). Repository implementations will be responsible for mapping SQLAlchemy models to pure Domain models before returning them to the Use Cases.

### Consequences
*   **Positive:** Business logic is completely decoupled from the database lifecycle. No unexpected lazy-loading crashes.
*   **Positive:** Domain models can be easily serialized to JSON for the API.
*   **Negative:** Requires writing mapping code (e.g., `return ChatMessage(role=sql_msg.role, content=sql_msg.content)`).

## ADR 009: Polymorphic Message Content for Multimodal Edge Cases
**Status:** Accepted

### Context
Users need to upload images and documents.
*   OpenAI expects images as a URL or base64 string inside an `image_url` object.
*   Anthropic expects base64 data inside a `source` object and strictly requires the `media_type` (e.g., `image/jpeg`).
*   Gemini expects an `inline_data` object.

### Decision
We will change the Domain `ChatMessage.content` from a simple `str` to a `Union[str, List[ContentPart]]`. We will define polymorphic domain entities: `TextPart`, `ImagePart`, and `DocumentPart`.
The Adapters will iterate through these parts and construct the provider-specific arrays.

### Consequences
*   **Positive:** The frontend and Use Cases only deal with a standard `ImagePart(base64, mime_type)`.
*   **Negative:** Adapters become slightly more complex, requiring type-checking (`isinstance(part, ImagePart)`) during payload construction.