## 1. Project Architecture & Organization
Do not put everything in one file. Treat a Reflex app like a standard modern web application.

*   **Modularize by Feature:** Group your code by domain, not just by file type.
    ```text
    my_app/
    ├── components/      # Reusable UI elements (buttons, navbars)
    ├── pages/           # Page-level components (dashboard.py, login.py)
    ├── state/           # Global and sub-states
    ├── models/          # Database schemas (SQLModel/SQLAlchemy)
    └── utils/           # Helper functions, constants
    ```
*   **Separate UI from Logic:** Keep your `rx.Component` functions pure where possible. Pass state variables as arguments rather than hardcoding `State.var` inside the component.

## 2. State Management (The Golden Rules)
The `rx.State` is the brain of your app, but it is also the primary bottleneck if misused.

*   **Use Sub-States:** Never use a single monolithic `State` class. Inherit from `rx.State` to create isolated sub-states (e.g., `AuthState`, `DashboardState`). Reflex only syncs the state that is actively being used on the current page.
*   **Leverage Computed Vars (`@rx.var`):** If a value can be derived from existing state variables, do not create a new state variable. Use `@rx.var`. This prevents unnecessary WebSocket updates and keeps the source of truth clean.
    ```python
    class CartState(rx.State):
        items: list[dict] = []

        @rx.var
        def total_price(self) -> float:
            return sum(item['price'] for item in self.items)
    ```
*   **Keep Payloads Small:** Do not store massive datasets (like a 10,000-row Pandas DataFrame) directly in a state variable that gets rendered. Paginate data or use backend-only variables (prefix with `_` like `_my_data`) so they aren't serialized over the WebSocket.

## 3. Performance & The WebSocket Bridge
Every state mutation requires a round-trip over the WebSocket. Optimize for this.

*   **Client-Side Vars for UI Toggles:** For simple UI interactions (opening a modal, toggling a sidebar), do not use server state. Use client-side state to avoid network latency.
*   **Yield for UI Updates:** If you have a long-running backend task, `yield` intermediate states so the frontend updates in real-time (e.g., showing a progress bar).
*   **Background Tasks (`@rx.background`):** For heavy processing (AI inference, large DB queries), use background tasks so you don't block the main async event loop.

## 4. React Interoperability (Custom Components)
Reflex is a bridge to React. Use the bridge wisely.

*   **Don't Reinvent the Wheel:** If you need complex client-side interactions (Drag-and-Drop, rich text editors, complex charts), **do not** try to build them from scratch using basic Reflex primitives.
*   **Wrap React Libraries:** Create custom `rx.Component` classes that wrap existing React/NPM libraries. Let React handle the 60fps DOM manipulations, and only send events to Python when persistence is required (e.g., `on_drag_end`, `on_save`).

## 5. Database & Async Operations
*   **Async by Default:** Reflex runs on an async event loop (FastAPI/Starlette under the hood). Use async database drivers and `async def` for your event handlers whenever performing I/O operations.
*   **Connection Pooling:** Ensure your `rxconfig.py` is set up with proper database connection pooling (e.g., via SQLAlchemy) to handle multiple concurrent WebSocket connections in production.
