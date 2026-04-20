# Reflex Shiki & Theme Rules for LLM Code Generation

## 1. `rx.code_block` vs `ShikiHighLevelCodeBlock`

| | `rx.code_block` | `ShikiHighLevelCodeBlock` |
|---|---|---|
| Backend | Prism (legacy) | Shiki (modern) |
| `language` type | `Literal[...]` — static only | `Var[LiteralCodeLanguage]` — accepts reactive Vars |
| `language=None` | crashes at compile time | handled gracefully (falls back to "python") |
| `theme` type | `str` (Prism theme name) | `Var[LiteralCodeTheme]` — accepts reactive Vars |
| Used by `rx.markdown` internally | NO | YES |

**Rule:** Never use `rx.code_block` inside a `component_map` function. Use `ShikiHighLevelCodeBlock.create(...)` instead.

```python
from reflex.components.datadisplay.shiki_code_block import ShikiHighLevelCodeBlock

def _code_block(text, **props):
    language = props.get("language")  # Var[str] at runtime; None during mock compilation
    return ShikiHighLevelCodeBlock.create(
        text,
        language=language,   # None is safe — skipped, not passed to Shiki
        theme=...,
        show_line_numbers=False,
        wrap_long_lines=True,
        width="100%",
    )
```

---

## 2. `rx.markdown` component_map keys

```
"code"  →  inline code only  (`backtick text`)
"pre"   →  fenced code blocks (``` ... ```)   ← use this for syntax highlighting
```

**Rule:** Always register the code block renderer under `"pre"`, not `"code"`.

```python
rx.markdown(content, component_map={"pre": _code_block})
```

**Why:** Reflex's `format_component_map()` always generates the `"pre"` handler via `_get_codeblock_fn_var()`. The `"code"` key is ignored for block rendering.

---

## 3. Language prop in the "pre" handler

When Reflex calls the `"pre"` component_map function, it passes:
- `text` — code content as a `Var[str]`
- `props["language"]` — language string already extracted from the fenced block header (e.g. `"python"`, `"javascript"`, or `""`)

**Rule:** Do NOT parse `className` to extract language. Use `props.get("language")` directly.

```python
# WRONG — works for "code" handler, not "pre"
lang = props.get("className", "").replace("language-", "")

# CORRECT — use for "pre" handler
language = props.get("language")  # Var at runtime, None during mock compilation
```

During mock compilation (Reflex calls the function with `_MOCK_ARG` to gather imports), `props` is empty, so `props.get("language")` returns `None`. `ShikiHighLevelCodeBlock.create` handles `language=None` by skipping the prop.

---

## 4. Shiki theme names (NOT Prism names)

`ShikiHighLevelCodeBlock` uses **Shiki** themes. These are different from Prism themes.

### Light themes
| Shiki name | Description |
|---|---|
| `github-light` | GitHub light (default recommended for light mode) |
| `github-light-default` | GitHub light default |
| `one-light` | Atom One Light |
| `light-plus` | VS Code Light+ |
| `min-light` | Minimal light |
| `solarized-light` | Solarized Light |
| `catppuccin-latte` | Catppuccin Latte |
| `vitesse-light` | Vitesse Light |
| `snazzy-light` | Snazzy Light |

### Dark themes
| Shiki name | Description |
|---|---|
| `nord` | Nord (default recommended for dark mode) |
| `one-dark-pro` | Atom One Dark Pro |
| `dracula` | Dracula |
| `night-owl` | Night Owl |
| `dark-plus` | VS Code Dark+ |
| `github-dark` | GitHub Dark |
| `github-dark-default` | GitHub Dark Default |
| `material-theme-ocean` | Material Ocean |
| `tokyo-night` | Tokyo Night |
| `catppuccin-mocha` | Catppuccin Mocha |
| `ayu-dark` | Ayu Dark |

### Common wrong Prism names to avoid
| WRONG (Prism) | CORRECT (Shiki) |
|---|---|
| `ghcolors` | `github-light` |
| `vs` | `light-plus` |
| `solarizedlight` | `solarized-light` |
| `one-dark` | `one-dark-pro` |
| `material-oceanic` | `material-theme-ocean` |
| `vsc-dark-plus` | `dark-plus` |
| `atom-dark` | *(no equivalent — use `one-dark-pro`)* |
| `gruvbox-light` | *(not available in Shiki)* |

---

## 5. Dynamic (reactive) theme switching

`ShikiHighLevelCodeBlock` passes `theme` to Shiki's `codeToHtml` in a `useEffect` with `theme` in the dependency array, so it IS reactive to prop changes.

**Correct pattern — per-mode theme stored in LocalStorage:**

```python
# state.py
code_theme: str = rx.LocalStorage("nord", name="code_theme_v2")
light_code_theme: str = rx.LocalStorage("github-light", name="light_code_theme_v2")

def set_code_theme(self, theme: str): self.code_theme = theme
def set_light_code_theme(self, theme: str): self.light_code_theme = theme
```

```python
# ui.py — in _code_block
theme=rx.color_mode_cond(ChatState.light_code_theme, ChatState.code_theme),
```

**Rule:** Use `_v2` (or versioned) LocalStorage keys when changing from Prism to Shiki theme names, to flush stale values from the browser.

---

## 6. App-level theme for dark/light mode

```python
# mychat_reflex.py
app = rx.App(
    theme=rx.theme(
        appearance="inherit",   # NOT "light" or "dark" — lets color mode control it
        ...
    )
)
```

**Rule:** `appearance="light"` or `appearance="dark"` locks the theme and makes `rx.color_mode.button()` ineffective. Always use `"inherit"` to allow user switching.

---

## 7. Dark mode Tailwind classes in Reflex

Since Reflex uses `TailwindV4Plugin` and `assets/styles.css` is served statically (not Tailwind-processed), `dark:` variants are unreliable. Use `rx.color_mode_cond()` instead.

```python
# WRONG — dark: variants may not work with TailwindV4Plugin static CSS
class_name="bg-white dark:bg-gray-900"

# CORRECT — use rx.color_mode_cond as a list entry in class_name
class_name=["static-layout-classes", rx.color_mode_cond("bg-white text-gray-800", "bg-gray-900 text-gray-100")]
```

---

## 8. Color mode toggle button

```python
rx.color_mode.button()          # icon-only sun/moon toggle (Radix default)
rx.color_mode.button(size="2")  # with size prop
rx.color_mode_cond(light=..., dark=...)  # conditional rendering by mode
rx.toggle_color_mode            # event handler for manual wiring
```

**Rule:** Place `rx.color_mode.button()` anywhere in the layout. It renders as a moon/sun icon and requires no additional state.

---

## 9. Streaming + Shiki: jiggling and partial-language errors

**Problem:** During LLM streaming, every chunk triggers `useEffect([..., code, language, ...])` in Shiki's `code.js`. This causes:
- **Flicker/jiggling** — async `codeToHtml` → blank → rendered → blank... on every character
- **ShikiError: Language `docke` not included** — partial language names are sent while the LLM streams ` ```dockerfile` character by character

**Fix:** Modify `.web/components/shiki/code.js` (Reflex places this file once; it is not regenerated on each run):

```javascript
import { useEffect, useState, useRef, createElement } from "react";
import { codeToHtml } from "shiki";

export function Code({ code, theme, language, transformers, decorations, ...divProps }) {
  const [codeResult, setCodeResult] = useState("");
  const debounceRef = useRef(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const result = await codeToHtml(code, { lang: language || "text", theme, transformers, decorations });
        setCodeResult(result);
      } catch (_) {
        try {
          const result = await codeToHtml(code, { lang: "text", theme });
          setCodeResult(result);
        } catch (_2) {
          setCodeResult(`<pre><code>${code}</code></pre>`);
        }
      }
    }, 150);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [code, language, theme, transformers, decorations]);

  return createElement("div", { dangerouslySetInnerHTML: { __html: codeResult }, ...divProps });
}
```

**Rules:**
- 150ms debounce suppresses rerenders during rapid streaming; adjust if needed
- `language || "text"` guards against empty/undefined language
- The outer try-catch retries with `"text"` on any Shiki language error
- This file lives at `.web/components/shiki/code.js` — re-apply if `.web/` is deleted or Reflex is upgraded
