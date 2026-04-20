# Known Issue: Section Collapse/Expand Jitter During LLM Streaming

**Status:** Unresolved
**Area:** `rx.markdown` + LLM streaming
**File:** `mychat_reflex/features/chat/state.py`, `mychat_reflex/features/chat/ui.py`

---

## Symptom

While the LLM is streaming a response, every time a new markdown section heading (`#`, `##`, etc.) appears in the output, the content below it visibly collapses and then expands. The effect repeats for each heading and makes the chat area jitter noticeably during generation.

---

## Root Cause

The jitter has two layers:

### Layer 1 — Unclosed code blocks misparse `#` comments as headings

When the LLM streams a fenced code block, the closing ` ``` ` has not arrived yet. `react-markdown` sees the partial content and tries to parse it. Any line starting with `#` inside the unclosed block is interpreted as a markdown heading:

```
Streaming state (closing ``` not yet received):

```python          ← opening fence, no closing fence yet
# Numbers         ← react-markdown sees this as <h1>Numbers</h1>
age = 25
```

When the closing ` ``` ` arrives on the next chunk, `react-markdown` re-parses the entire block and `# Numbers` becomes a code comment inside `<pre>`. The transition from heading (large font, large margins) to code comment (small monospace) is the visible collapse/expand.

### Layer 2 — Every streaming chunk re-renders the full markdown tree

`rx.markdown` re-renders on every `message.content` state update (which happens every ~12 characters). React-markdown rebuilds the component tree on each render. When a new heading element is added, siblings shift, and `ShikiHighLevelCodeBlock` instances may remount — resetting their internal `useState("")` and causing a blank flash before Shiki re-highlights.

---

## What Was Attempted

### Fix 1 — `_close_open_code_block` in streaming loop (`state.py`)
During streaming, appends `\n``` ` to `message.content` whenever the count of ` ``` ` is odd, so `react-markdown` always sees a closed block. Reverts to clean content on stream completion.

**Result:** Partially effective. Prevents `# comment` lines from rendering as headings. The section collapse/expand still occurs because of Layer 2 (full tree re-render on every chunk → heading elements resize the layout on each chunk arrival).

### Fix 2 — `safe_content` `@property` on `Message` model
Added a `@property` to `Message` to compute the closed content.

**Result:** Broke all message rendering. `@property` on `rx.Model` is **not** included in Pydantic's `model_dump()` serialization, so the Reflex frontend Var resolves to `undefined` → `rx.markdown(undefined)` renders nothing.

**Lesson:** Never use `@property` on `rx.Model` for values intended to be accessed as Reflex Vars in components. Use declared model fields or `@rx.var` on `rx.State` instead.

### Fix 3 — Shiki debounce in `.web/components/shiki/code.js`
Added 150ms debounce and error fallback for unknown/partial language names.

**Result:** Eliminated the Shiki `ShikiError: Language 'docke' not included` console errors and reduced some Shiki-specific flicker. Did not fix the markdown tree collapse/expand.

---

## Approaches Not Yet Tried

1. **Debounce the entire `rx.markdown` render** — render the message content only after a pause in streaming (e.g., 200ms of no new chunks). Requires a debounced display var in state separate from the raw `content` being accumulated. Tradeoff: typewriter effect would pause while Shiki catches up.

2. **Plain-text during streaming, markdown on completion** — use `rx.cond(ChatState.is_generating & is_last_message, rx.text(message.content), rx.markdown(message.content, ...))`. Eliminates all markdown parse jitter during generation; one layout shift when stream ends.

3. **Keyed components** — provide stable `key` props to `rx.foreach` items so React reconciles in-place instead of remounting on position shift. Reflex's `rx.foreach` does not currently expose a `key` parameter.

4. **Virtual DOM batching** — batch streaming updates into larger chunks (e.g., every 200ms rather than every 12 chars) to reduce re-render frequency. Would make the typewriter effect choppier.

---

## Affected Code Locations

| File | What to look at |
|---|---|
| `mychat_reflex/features/chat/state.py` | `handle_send_message` — `_close_open_code_block` call in streaming loop |
| `mychat_reflex/features/chat/ui.py` | `message_bubble` — `rx.markdown` with `component_map={"pre": _code_block}` |
| `.web/components/shiki/code.js` | Debounce + error fallback (custom, not Reflex-generated) |
