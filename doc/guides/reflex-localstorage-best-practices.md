# Reflex LocalStorage Best Practices

## Quick Reference

### ✅ Correct Pattern (UPDATED - String Storage)
```python
class MyState(rx.State):
    # ALWAYS store as strings in LocalStorage
    user_name: str = rx.LocalStorage("guest")
    theme: str = rx.LocalStorage("dark")
    font_size: str = rx.LocalStorage("14")  # String, not int!
    notifications: str = rx.LocalStorage("false")  # String, not bool!
    volume: str = rx.LocalStorage("0.8")  # String, not float!

    # Setters: Convert everything to strings
    def set_user_name(self, value):
        self.user_name = str(value)

    def set_font_size(self, value):
        self.font_size = str(value)

    def set_notifications(self, value):
        self.notifications = str(value).lower()  # "true" or "false"

    # Computed vars: Convert strings back to typed values
    @rx.var
    def font_size_int(self) -> int:
        try:
            return int(self.font_size)
        except (ValueError, TypeError):
            return 14

    @rx.var
    def notifications_bool(self) -> bool:
        return str(self.notifications).lower() in ('true', '1', 'yes')

    @rx.var
    def volume_float(self) -> float:
        try:
            return float(self.volume)
        except (ValueError, TypeError):
            return 0.8
```

### ❌ Common Mistakes

#### Mistake 1: Using Primitive Types in LocalStorage
```python
# BAD - Causes "Expected field 'X' to receive type 'float', but got LocalStorage" errors
temperature: float = rx.LocalStorage(0.7)
enable_feature: bool = rx.LocalStorage(False)
count: int = rx.LocalStorage(0)
```
**Why it fails:** When Reflex hydrates state from browser storage, it creates LocalStorage proxy objects that don't match primitive type annotations.

#### Mistake 2: Not Converting in Setters
```python
# BAD - Stores non-string values
def set_temperature(self, value):
    self.temperature = value  # If value is float, this breaks!

# GOOD - Always convert to string
def set_temperature(self, value):
    self.temperature = str(value)
```

#### Mistake 3: Using Raw Fields Instead of Computed Vars
```python
# BAD - String value used where int is needed
if self.font_size > 20:  # Compares strings: "20" > "100" = False!
    ...

# GOOD - Use typed computed var
if self.font_size_int > 20:  # Compares ints: 100 > 20 = True!
    ...
```

## How It Works

### Storage vs. Value Types
```python
theme: str = rx.LocalStorage("dark")
#      ^^^                     ^^^^^^
#   VALUE type              INITIAL value
#   (what the field holds)  (how it's stored)
```

### Reflex Type Checking
When you call `MyState.set_theme("light")`:
1. Reflex checks: `isinstance("light", str)` ✅
2. LocalStorage handles browser persistence automatically
3. Value is available as `MyState.theme` (acts like a string)

### Field Introspection
```python
field = MyState.get_fields()['theme']
field.outer_type_  # <class 'str'> - correct!
field.default      # 'dark' (LocalStorage instance)
```

## Advanced Patterns

### Custom Storage Keys
```python
# Use different key names in browser localStorage
user_pref: str = rx.LocalStorage("dark", name="user_theme_v2")
```

### Sync Across Tabs
```python
# Changes propagate to other browser tabs
settings: str = rx.LocalStorage("default", sync=True)
```

### Computed Values
```python
temperature: float = rx.LocalStorage(0.7)

@rx.var
def temperature_display(self) -> str:
    return f"{self.temperature:.1f}"
```

### Type Conversions
```python
# LocalStorage stores primitives correctly
count: int = rx.LocalStorage(0)

def increment(self):
    self.count += 1  # Works as expected

@rx.var
def count_doubled(self) -> int:
    return self.count * 2  # Type-safe
```

## Debugging Tips

### Enable Logging
```python
import logging
logger = logging.getLogger(__name__)

def set_theme(self, value):
    logger.info(f"Setting theme: {value!r} (type={type(value).__name__})")
    self.theme = value
```

### Inspect Field Types
```python
# In development console or debugger:
fields = MyState.get_fields()
for name, field in fields.items():
    if hasattr(field.default, '__class__'):
        if 'LocalStorage' in str(field.default.__class__):
            print(f"{name}: outer_type={field.outer_type_}, default={field.default!r}")
```

### Check Browser Storage
```javascript
// In browser DevTools console:
console.log(localStorage);
// Should see your stored values
```

## Migration Guide

### From Untyped to Typed
```python
# Before (broken):
theme = rx.LocalStorage("dark")

# After (fixed):
theme: str = rx.LocalStorage("dark")
```

### Version Bumping (Force Refresh)
```python
# If users have old cached values:
theme: str = rx.LocalStorage("dark", name="theme_v2")
#                                          ^^^^^^^^ new key
```

### Clearing Old Cache
```python
# Server-side migration (if needed):
async def on_load(self):
    # Force reset to defaults if needed
    if some_condition:
        self.theme = "dark"  # Overwrites old value
```

## Common Use Cases

### User Preferences
```python
class SettingsState(rx.State):
    theme: str = rx.LocalStorage("dark")
    language: str = rx.LocalStorage("en")
    sidebar_open: bool = rx.LocalStorage(True)
    font_scale: float = rx.LocalStorage(1.0)
```

### Form Drafts
```python
class FormState(rx.State):
    draft_title: str = rx.LocalStorage("")
    draft_content: str = rx.LocalStorage("")
    last_saved: str = rx.LocalStorage("")
```

### UI State
```python
class UIState(rx.State):
    active_tab: str = rx.LocalStorage("home")
    zoom_level: int = rx.LocalStorage(100)
    panel_sizes: str = rx.LocalStorage("300,600,300")  # Comma-separated
```

## Testing

### Unit Tests
```python
def test_localstorage_field():
    state = MyState()
    assert isinstance(state.theme, str)
    state.set_theme("light")
    assert state.theme == "light"
```

### Integration Tests
```python
# Use Reflex testing utilities
from reflex.testing import AppHarness

async def test_theme_persistence():
    async with AppHarness(app) as harness:
        # Interact with UI
        await harness.click("#theme-toggle")
        # Check state
        assert harness.state.theme == "light"
```

## Resources

- [Reflex State Documentation](https://reflex.dev/docs/state/overview/)
- [LocalStorage API Reference](https://reflex.dev/docs/api-reference/storage/)
- Internal: `doc/backlog/bugs/fix2-solution.md`
