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

### 5. Hook-Safe Nested Renderers (`component_map`, `rx.foreach`, callbacks)
Some Reflex APIs accept Python functions that are later compiled into frontend render callbacks. Treat these functions as **hook-sensitive boundaries**.

*   **The Rule:** Any function passed into `rx.markdown(component_map=...)`, `rx.foreach(...)`, or similar nested render APIs must be **pure, static, and hook-free**.
*   **Never read reactive state inside these callbacks.** Avoid:
    *   `SomeState.some_var`
    *   computed vars like `SomeState.active_theme`
    *   `rx.color_mode_cond(...)`
    *   any helper that depends on frontend context
*   **Why?** Reflex may compile these helpers into React functions that call `useContext(...)`. If such a function is invoked during list rendering or conditional rendering, React can detect a changing hook order and throw warnings like: **"React has detected a change in the order of Hooks"**.
*   **High-risk combination:** `rx.markdown(component_map=...)` inside `rx.foreach(...)` where the component-map callback references `State`.
*   **Safe pattern:** Compute reactive values outside the callback, or use static values inside the callback only.

```python
# ❌ BAD: renderer callback reads reactive state.
def code_block(text, **props):
    return ShikiHighLevelCodeBlock.create(
        text,
        language=props.get("language"),
        theme=ChatState.active_code_theme,
    )

rx.foreach(ChatState.messages, lambda message: rx.markdown(
    message.content,
    component_map={"pre": code_block},
))

# ✅ BETTER: keep nested renderer pure and non-reactive.
def code_block(text, **props):
    return ShikiHighLevelCodeBlock.create(
        text,
        language=props.get("language"),
        theme="nord",
    )
```

*   **Debugging rule:** If React reports hook-order problems, inspect the generated `.web/app/routes/*.jsx` output and search for nested helper functions that unexpectedly contain `useContext(...)`.

### 6. Event Handler Yielding (UX Best Practice)
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



### 7. The "Non-Blocking Hydration" Pattern
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

### 8. WebSocket Traffic Control (Debouncing)
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
        on_change=SearchState.run_search,
        debounce_timeout=300  # Native Reflex prop! Much cleaner.
    )
```

### 9. The Background Task Pattern (`@rx.background`)
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

### 10. Component Factories (Pythonic HOCs)
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

### 11. LocalStorage State Variables (v0.8+)
**The Problem:** You want UI preferences (theme, model selection, settings) to persist across browser sessions without database overhead.
**The Solution:** Use `rx.LocalStorage` for client-side persistence.

**Critical Rules:**
1. **No Type Hints:** Do NOT add type hints to LocalStorage variables. Reflex infers types from default values.
2. **No Direct Comparisons:** Cannot compare LocalStorage values directly in `@rx.var` computed properties.
3. **Use Type Conversion Methods:** Call `.bool()`, `.to(int)`, or convert in computed properties.

```python
# ❌ BAD: Type hints cause "Expected field to receive type X, got LocalStorage" errors
class MyState(rx.State):
    temperature: float = rx.LocalStorage(0.7, name="temperature")
    enable_feature: bool = rx.LocalStorage(False, name="feature")

# ✅ GOOD: No type hints
class MyState(rx.State):
    temperature = rx.LocalStorage(0.7, name="temperature")
    enable_feature = rx.LocalStorage(False, name="feature")

    # Create computed property for comparisons
    @rx.var
    def temperature_int(self) -> int:
        try:
            return int(self.temperature)
        except (ValueError, TypeError):
            return 70  # default
```

**Component Usage:**
```python
# ❌ BAD: Direct comparison fails
rx.cond(
    ChatState.reasoning_budget >= 16000,  # TypeError: comparison not supported
    "High",
    "Low"
)

# ✅ GOOD: Use computed property
rx.cond(
    ChatState.reasoning_budget_int >= 16000,
    "High",
    "Low"
)

# ❌ BAD: Switch expects bool, gets LocalStorage
rx.switch(
    checked=ChatState.enable_feature,  # TypeError: expected bool
    on_change=ChatState.set_enable_feature,
)

# ✅ GOOD: Call .bool() method
rx.switch(
    checked=ChatState.enable_feature.bool(),
    on_change=ChatState.set_enable_feature,
)
```

**When to Use LocalStorage vs Database:**
- **LocalStorage:** UI preferences, theme, layout, recently selected options (per-browser)
- **Database:** User data, chat history, notes, settings that sync across devices

### 12. Dynamic Dependency Injection at Runtime
**The Problem:** You need to switch LLM providers (Anthropic ↔ OpenAI) without restarting the application.
**The Solution:** Use the Service Locator pattern with runtime adapter instantiation.

```python
class ChatState(rx.State):
    selected_model = rx.LocalStorage("claude-sonnet-4-5", name="model")

    async def _ensure_correct_adapter(self, model: str):
        """Switch adapter if model changed."""
        import os
        from infrastructure.llm_adapters import AnthropicAdapter, OpenAIAdapter

        current_service = AppContainer.resolve_llm_service()
        current_model = getattr(current_service, "model", None)

        # Skip if already correct
        if current_model == model:
            return

        # Determine which adapter to use
        if model.startswith("claude"):
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            adapter = AnthropicAdapter(api_key=api_key, model=model)
        elif model.startswith(("gpt", "o1")):
            api_key = os.getenv("OPENAI_API_KEY", "")
            adapter = OpenAIAdapter(api_key=api_key, model=model)

        # Register new adapter (old one gets garbage collected)
        AppContainer.register_llm_service(adapter)

    @rx.event(background=True)
    async def handle_send_message(self):
        async with self:
            current_model = self.selected_model

        # Switch adapter if needed
        await self._ensure_correct_adapter(current_model)

        # Now use case will get correct adapter
        llm_service = AppContainer.resolve_llm_service()
        # ... rest of message handling
```

**Benefits:**
- No app restart required
- Clean resource management (old adapters GC'd)
- Preserves DI architecture
- Works with background tasks

**Gotchas:**
- Always check current adapter before creating new one (avoid unnecessary instantiation)
- API keys must be available in environment at runtime
- Read the model selection in `async with self:` block before switching

### 13. Popover Components and Interactive Controls
**The Problem:** Building dropdown menus, modals, or tooltips with proper accessibility and positioning.
**The Solution:** Use `rx.popover` components following Reflex's structure.

**Pattern:**
```python
def model_selector() -> rx.Component:
    return rx.popover.root(
        rx.popover.trigger(
            rx.button("Select Model"),
        ),
        rx.popover.content(
            rx.box(
                rx.button(
                    "Option 1",
                    on_click=lambda: State.set_option("opt1"),
                ),
                rx.button(
                    "Option 2",
                    on_click=lambda: State.set_option("opt2"),
                ),
            ),
        ),
    )
```

**Best Practices:**
- Trigger should be a single interactive element (button, icon)
- Content should have explicit width (`min-w-[200px]`) to prevent wrapping
- Use `rx.cond` inside popover to show selection state (highlight selected item)
- Popovers auto-close on outside click (no manual state needed)
- For nested conditional content, use `rx.cond` not Python `if`

### 14. Computed Properties vs Regular Methods
**The Problem:** Confusion about when to use `@rx.var` vs regular methods in State.
**The Solution:** Follow these rules strictly.

**Use `@rx.var` (Computed Property) when:**
- Deriving display values from state (e.g., formatting, mapping IDs to names)
- Value is read-only and deterministic
- Needed in UI rendering (text, conditions, styling)
- No side effects

**Use Regular Methods when:**
- Handling events (clicks, changes, submissions)
- Mutating state
- Making API calls or database queries
- Side effects are required

```python
class ChatState(rx.State):
    selected_model = rx.LocalStorage("gpt-4o", name="model")

    # ✅ Computed property: derives display value
    @rx.var
    def model_display_name(self) -> str:
        names = {"gpt-4o": "GPT-4o", "claude-sonnet-4-5": "Claude Sonnet 4.5"}
        return names.get(str(self.selected_model), self.selected_model)

    # ✅ Regular method: mutates state (event handler)
    def set_selected_model(self, model: str):
        self.selected_model = model
```

**In UI:**
```python
# ✅ Access computed property directly (no parentheses)
rx.text(ChatState.model_display_name)

# ✅ Call event handler
rx.button("Change", on_click=lambda: ChatState.set_selected_model("gpt-4o"))
```

**Critical Error to Avoid:**
```python
# ❌ Calling regular method as if it were a computed property
rx.text(ChatState.get_model_name())  # Creates EventSpec, not string!

# ✅ Use @rx.var instead
@rx.var
def model_name(self) -> str:
    return self._get_model_name()
```
