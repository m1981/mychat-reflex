## ADR 002-V2: Native WebSocket Streaming via Reflex State
**Status:** Accepted (Replaces ADR 002)

### Context
Streaming LLM responses (like ChatGPT) requires pushing text chunks to the UI in real-time. Because we adopted the Full-Stack Monolith (ADR 011), we are using Reflex's native WebSocket reactivity instead of Server-Sent Events (SSE). However, yielding every single character from an LLM directly to `rx.State` can flood the WebSocket with hundreds of JSON diffs per second, causing the React frontend to freeze.

### Decision
We will use **Reflex's native WebSocket reactivity with Token Buffering**. The Use Case will yield raw text chunks. The `rx.State` (ViewModel) will accumulate these tokens in a buffer and only `yield` to update the UI every ~50 milliseconds or every 5-10 tokens.

### Consequences
*   **Positive:** Zero network protocol coding required (no manual SSE).
*   **Positive:** UI updates remain perfectly synchronized with the backend state without locking the browser's main thread.
*   **Negative:** Requires slightly more complex generator logic in the `rx.State` to manage the buffer.

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

*****

## ADR 014: Reflex State and UI Guidelines
**Status:** Accepted

### Context
Reflex compiles Python to React and synchronizes state via WebSockets. Improper use of Reflex state can lead to massive JSON payloads, frozen UIs, and compile-time bugs.

### Decision
We will strictly adhere to the following Reflex-specific patterns:
1.  **UI Logic Only:** `rx.State` classes will act strictly as ViewModels. They will not contain SQL queries or API calls; they will delegate to the Application Use Cases.
2.  **Background Streaming:** Any Use Case that takes longer than 200ms (e.g., LLM generation, Vector DB search) must be executed within an `@rx.background` task to prevent WebSocket locking.
3.  **Backend-Only Variables:** Any data retrieved from Use Cases that does not need to be rendered in the DOM (e.g., raw vector embeddings, database session objects) must be stored in variables prefixed with `_` to prevent WebSocket serialization.
4.  **Runtime Conditionals:** Standard Python `if/else` statements are banned for UI rendering logic. `rx.cond` or `rx.match` must be used to ensure React AST compilation is correct.

### Consequences
*   **Positive:** Guarantees a 60fps, non-blocking User Experience.
*   **Positive:** Prevents accidental data leaks to the browser.
*   **Negative:** Developers must learn the difference between compile-time Python and runtime Reflex state.
