# SuperChat Reflex — Coding Rules

## 1. Style system

**Single source of truth: `ui/primitives.py`**
- All theme-aware class strings live in the `T` dict. Never write `dark:` inline in feature files.
- Dark mode uses Tailwind `darkMode: "class"` (configured in `tailwind.config.js`). Reflex writes `.dark` on `<html>` automatically.
- Never use `cm()` / `cls()` helpers — they are deleted. Use plain `dark:` strings inside `T` only.

```python
# ✅ correct
class_name=T["pill_btn"]

# ❌ wrong
class_name=cls(TOOLBAR_TRIGGER_BASE, cm("bg-white", "bg-zinc-900"))
```

---

## 2. Element choice

| Need | Use | Never use |
|---|---|---|
| Precise sizing / styled button | `rx.el.button` | `rx.button(variant=...)` |
| Div / container | `rx.el.div` | `rx.box` |
| Behaviour (popover, switch, slider, select) | `rx.popover`, `rx.switch`, `rx.slider`, `rx.select` | — |
| Semantic layout | `rx.el.main`, `rx.el.aside`, `rx.el.header`, `rx.el.footer`, `rx.el.nav` | `rx.box` |

**Why:** Radix `rx.button` injects `rt-r-size-2` and `rt-variant-*` classes that override Tailwind sizing. `rx.el.button` has zero injected styles.

---

## 3. Primitives

Always use functions from `ui/primitives.py`. Never re-implement inline.

```python
from ...ui.primitives import T, pill_btn, icon_btn, icon_btn_square, card, popover, nav_item, footer_btn
```

| Function | Use case |
|---|---|
| `pill_btn(*children, on_click, extra)` | Toolbar pills (Tools, Run, Model, Think, Temp) |
| `icon_btn(icon, on_click, extra)` | Circular icon buttons (mic, plus) |
| `icon_btn_square(icon, on_click, extra)` | Square icon buttons (key) |
| `card(*children, extra)` | Raised card containers |
| `popover(trigger, content, min_width)` | Any Radix popover |
| `nav_item(*children, on_click)` | Sidebar chat/nav rows |
| `footer_btn(*children, on_click)` | Sidebar footer actions |

Adding a new reusable component? Add it to `ui/primitives.py` first, then use it.

---

## 4. Radix integration pattern

Use Radix components **for behaviour only**. Their triggers must always be `rx.el.button` (via a primitive), never `rx.button`.

```python
# ✅ correct
rx.popover.root(
    rx.popover.trigger(
        pill_btn(rx.icon("sparkles", size=15), rx.el.span("Model"))
    ),
    rx.popover.content(content, class_name=T["popover_panel"]),
)

# ❌ wrong — Radix styles bleed onto trigger
rx.popover.trigger(
    rx.button("Model", variant="ghost", class_name="h-8 px-3 ...")
)
```

---

## 5. Layout structure

```
rx.el.aside    → sidebar
rx.el.main     → chat area
  rx.el.header → chat header (top bar)
  rx.el.div    → chat history (scrollable)
  rx.el.footer → chat input (anchors to bottom of flex column)
```

The root layout is a flex row: `aside` + `main`. `main` is a flex column. `footer` naturally anchors at the bottom — no `mt-auto` needed.

---

## 6. Feature file rules

- Feature files (`chat/ui.py`, `workspace/ui.py`) import `T` and primitives only. No raw `dark:` strings.
- `chat/ui.py` imports `ChatState` only.
- `workspace/ui.py` imports `ChatState` temporarily (FIXME — Phase 4: extract `WorkspaceState`).
- Cross-feature communication uses Reflex event chains, never direct state imports.

---

## 7. Adding a new token

1. Add the full light + dark class string to `T` in `ui/primitives.py`.
2. Use `T["your_token"]` in the component.
3. Never add a token in a feature file.

```python
# ui/primitives.py
T = {
    ...
    "my_new_token": "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
}
```

---

## 8. Checklist before committing UI code

- [ ] No `rx.button(variant=...)` in styled components
- [ ] No `rx.box` — replaced with `rx.el.div` or semantic element
- [ ] No `cm()` / `cls()` calls
- [ ] No `dark:` strings outside `ui/primitives.py`
- [ ] No inline style dicts with CSS variable strings (`var(--color-*)`) — those only exist in the widget sandbox
- [ ] New reusable element added to `ui/primitives.py`, not inline
- [ ] Feature file imports only its own state class
