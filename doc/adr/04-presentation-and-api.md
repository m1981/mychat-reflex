## ADR 002: Server-Sent Events (SSE) with Structured JSON for Chat
**Status:** Accepted

### Context
The application requires a ChatGPT-like streaming experience. The UI needs to display intermediate states (e.g., "Searching documents...", "Found 3 sources") before and during the text generation. Streaming raw text makes it impossible for the frontend to parse metadata, citations, or tool usage. WebSockets provide bidirectional streaming but introduce significant state-management overhead.

### Decision
We will use **Server-Sent Events (SSE)** via FastAPI's `StreamingResponse`. The backend will yield structured JSON payloads (e.g., `{"event": "sources", "data": [...]}` and `{"event": "chunk", "data": "text"}`) rather than raw strings.

### Consequences
*   **Positive:** Unidirectional flow is perfectly suited for LLM generation.
*   **Positive:** Frontend can easily parse JSON to update distinct UI components (citations vs. markdown text).
*   **Negative:** Requires custom parsing logic on the frontend to accumulate the JSON chunks.

***

## ADR 013: MVVM Pattern for Frontend Presentation
**Status:** Accepted

### Context
The application requires a highly interactive User Interface. It must handle real-time streaming text, optimistic UI updates (showing a message before the database confirms it), and synchronized state between the Chat area and the Notes sidebar. Traditional MVC (where the server renders static HTML views) cannot support this level of interactivity.

### Decision
We will utilize the **MVVM (Model-View-ViewModel)** pattern for the presentation layer. 
*   **Model:** The backend Domain Entities and Use Cases.
*   **View:** The UI components (React components or Reflex UI functions).
*   **ViewModel:** The frontend State manager (e.g., Reflex `State` classes or React hooks/Zustand). The ViewModel will hold the current state of the UI, handle user intents, call the backend APIs, and automatically trigger View updates when data changes.

### Consequences
*   **Positive:** Clean separation of concerns. UI components (Views) remain "dumb" and only care about rendering, while the ViewModel handles the complex logic of accumulating SSE streaming chunks.
*   **Positive:** Highly reactive UX. When a Note is created in the Chat ViewModel, the Notes Sidebar ViewModel can react and update instantly.
*   **Negative:** Requires careful state management to avoid memory leaks or infinite re-render loops during high-speed text streaming.
