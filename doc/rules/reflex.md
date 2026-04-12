### 1. Tooling & Environment
In v0.8+, Reflex relies heavily on Python type hints to compile the frontend correctly.
*   **Strict Type Checking:** You *must* use a type checker like `pyright` or `mypy`. Reflex uses your type annotations (e.g., `list[dict]`, `str`, `int`) to determine how to serialize data over the WebSocket and what React prop types to generate. Missing types will cause silent frontend bugs.
*   **Linting with Ruff:** Use `ruff` for formatting and linting. It’s lightning-fast and integrates perfectly with the modern `uv` workflow you are already using.
*   **Environment Variables:** Never hardcode secrets. Use `python-dotenv` or Reflex's built-in config to load `.env` files. Reflex v0.8+ handles environment variables cleanly between the build step and runtime.

### 2. The "Backend-Only" Variable Rule (Crucial)
The #1 mistake new Reflex developers make is accidentally sending massive amounts of data to the React frontend, crashing the browser.
*   **The Rule:** If the React frontend doesn't need to *display* it, prefix the variable with an underscore (`_`).
*   **Why?** Variables starting with `_` are **backend-only**. They are not serialized into JSON and are not sent over the WebSocket.
```python
class DataState(rx.State):
    # Sent to the browser (keep it small!)
    display_table: list[dict] = []

    # Stays on the server (can be a massive 2GB Pandas DataFrame)
    _raw_data: pd.DataFrame = None
```

### 3. Debugging the WebSocket Bridge
When things break in Reflex, it's rarely a standard Python error. It's usually a state synchronization issue.
*   **Stop using `print()` for UI issues:** If you want to see what the frontend is doing, use `rx.console_log(self.my_var)` in your event handlers. This prints the state directly to the *browser's* developer console.
*   **Watch the Network Tab:** Open your browser's DevTools, go to the Network tab, and filter by `WS` (WebSockets). Click on the active connection and look at the "Messages". You will see exactly what JSON payloads Python is sending to React. If the payload is 5MB, you have a state architecture problem.

### 4. UI Compilation vs. Runtime Execution
You must understand *when* your code runs.
*   Your `def index() -> rx.Component:` function runs **exactly once** during the `reflex run` compilation phase. It generates the React AST (Abstract Syntax Tree).
*   Therefore, you **cannot** use standard Python `if/else` statements to conditionally render UI based on `rx.State` variables, because the state doesn't exist at compile time!
*   **Best Practice:** Always use Reflex's conditional rendering components (`rx.cond` or `rx.match`) when depending on state variables.

```python
# ❌ BAD: This evaluates at compile time and will fail or behave unexpectedly.
def my_page():
    if State.is_logged_in:
        return rx.text("Welcome")
    return rx.text("Please log in")

# ✅ GOOD: This compiles to a React ternary operator and evaluates at runtime.
def my_page():
    return rx.cond(
        State.is_logged_in,
        rx.text("Welcome"),
        rx.text("Please log in")
    )
```

### 5. Event Handler Yielding (UX Best Practice)
If you have an event handler that takes more than 200ms (like querying a database or calling an OpenAI API), you must yield intermediate states to keep the UI responsive.

```python
class ChatState(rx.State):
    is_loading: bool = False
    response: str = ""

    async def fetch_ai_response(self):
        # 1. Set loading to True and immediately update the UI
        self.is_loading = True
        yield

        # 2. Do the heavy lifting (UI is currently showing a spinner)
        result = await call_openai_api()

        # 3. Update the final state
        self.response = result
        self.is_loading = False
        # Implicit yield at the end of the function
```



### 6. The "Non-Blocking Hydration" Pattern
**The Problem:** If you fetch database records in your `rx.State` initialization or block the main thread when a page loads, the user stares at a blank white screen while the server thinks.
**The Solution:** Render the UI instantly with empty/skeleton data, then use the page's `on_load` event to fetch data asynchronously using `yield`.

```python
class DashboardState(rx.State):
    metrics: list[dict] = []
    is_loading: bool = True

    async def fetch_initial_data(self):
        # 1. UI is already visible (showing skeletons). We yield to ensure is_loading=True is sent.
        self.is_loading = True
        yield

        # 2. Await the heavy DB call without blocking the event loop
        self.metrics = await db.get_heavy_metrics()

        # 3. Turn off loading state
        self.is_loading = False
        # Implicit yield updates the UI with real data

# In your page definition:
@rx.page(route="/dashboard", on_load=DashboardState.fetch_initial_data)
def dashboard():
    return rx.cond(
        DashboardState.is_loading,
        rx.skeleton(width="100%", height="400px"), # Instant render
        render_metrics_chart()                     # Renders after DB call
    )
```

### 7. WebSocket Traffic Control (Debouncing)
**The Problem:** You build a live search bar. If a user types "Reflex" at 100 WPM, the frontend fires 6 WebSocket events in half a second. The server tries to run 6 database queries simultaneously, causing race conditions and UI jitter.
**The Solution:** Always debounce text inputs that trigger backend logic.

```python
class SearchState(rx.State):
    search_query: str = ""
    results: list[str] = []

    def run_search(self, query: str):
        self.search_query = query
        self.results = db.search(query)

def search_bar():
    return rx.input(
        placeholder="Search...",
        # Wait 300ms after the user STOPS typing before sending the WS event
        on_change=rx.debounce(SearchState.run_search, debounce_timeout=300)
    )
```

### 8. The Background Task Pattern (`@rx.background`)
**The Problem:** You need to generate a PDF report or run an AI model that takes 30 seconds. If you do this in a normal event handler, you lock the `rx.State`. The user can't click other buttons, and the WebSocket might timeout.
**The Solution:** Use `@rx.background`. This detaches the function from the main state lock, allowing the user to continue using the app while the server works in the background.

```python
import asyncio

class ReportState(rx.State):
    progress: int = 0
    is_generating: bool = False

    @rx.background
    async def generate_report(self):
        # Background tasks require you to explicitly lock the state when modifying it
        async with self:
            self.is_generating = True
            self.progress = 0

        for i in range(10):
            await asyncio.sleep(1) # Simulating heavy work

            # Lock state only briefly to update progress
            async with self:
                self.progress = (i + 1) * 10

        async with self:
            self.is_generating = False
```

### 9. Component Factories (Pythonic HOCs)
**The Problem:** You have 15 different forms in your app, and you are copying and pasting `rx.vstack`, `rx.text`, and `rx.input` with the same styling everywhere.
**The Solution:** Treat Python functions like React Higher-Order Components (HOCs). Create factory functions that return configured `rx.Component` objects.

```python
# utils/components.py
def form_field(label: str, placeholder: str, on_change_handler) -> rx.Component:
    """A commercial-grade, standardized form field."""
    return rx.vstack(
        rx.text(label, weight="bold", size="2", color="gray.11"),
        rx.input(
            placeholder=placeholder,
            on_change=on_change_handler,
            width="100%",
            variant="surface",
            radius="md"
        ),
        align_items="start",
        width="100%",
        spacing="1"
    )

# In your page:
def login_page():
    return rx.box(
        form_field("Email Address", "name@company.com", AuthState.set_email),
        form_field("Password", "••••••••", AuthState.set_password),
    )
```
