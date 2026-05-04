# Product Specification: Chat Feature

**Feature**: Core AI Chat Conversation
**Status**: Active — MVP shipped, polishing UX
**Priority**: P0 (Critical Path)
**Last Updated**: 2026-05-04

> **Authoritative cross-references**
> - Architecture: [`doc/2-architecture/reflex-monolith-architecture.md`](../2-architecture/reflex-monolith-architecture.md)
> - DB schema: [`doc/3-reference/database-schema.md`](../3-reference/database-schema.md)
> - LocalStorage UX rules: [`doc/guides/reflex-localstorage-best-practices.md`](../guides/reflex-localstorage-best-practices.md)
> - ADRs: [`doc/adr/`](../adr/)

---

## 1. Feature Overview

### 1.1 Business Value
Enable users to have real-time conversations with AI assistants (Anthropic Claude / OpenAI GPT) using a ChatGPT-like interface with streaming responses, multi-model selection, optional extended-thinking, and Markdown + syntax-highlighted code rendering.

### 1.2 User Stories

**US-1: Send Message to AI**
```gherkin
As a user
I want to send a message to the AI assistant
So that I can get intelligent responses to my questions

Acceptance Criteria:
- User can type a message in the input field
- User can press Enter or click Send to submit
- Message appears in chat history immediately (optimistic update)
- Input field clears after sending
- Send button is disabled while AI is generating
```

**US-2: Receive Streaming AI Response**
```gherkin
As a user
I want to see the AI response appear in real-time
So that I know the system is working and can start reading early

Acceptance Criteria:
- AI response appears as a new message bubble below the user message
- Text streams in (in ~40-character batches — see §3.3)
- Code fences render progressively without breaking Markdown mid-stream
- Response completes and becomes static when done
```

**US-3: View Conversation History**
```gherkin
As a user
I want to see all previous messages in the current conversation
So that I can review the context and previous answers

Acceptance Criteria:
- Messages are displayed in chronological order (oldest at top)
- User messages appear on the right with avatar
- AI messages appear on the left with an AI icon
- Timestamps are shown for each message
- Conversation persists across page refreshes
- The model has memory of prior turns within the conversation
  (transcript is rebuilt and re-sent on each turn — see §3.4)
```

**US-4: Choose Model & Reasoning Settings**
```gherkin
As a user
I want to pick a model, temperature, and (where supported) extended-thinking budget
So that I can trade off speed, cost, and reasoning depth

Acceptance Criteria:
- Model selector shows the configured models (Claude family + GPT family)
- Selected model name is shown in the input bar
- Temperature is adjustable via popover
- Extended-thinking can be toggled on/off
- When enabled, a reasoning-budget popover appears
- All preferences persist across page reloads (LocalStorage)
- Switching to claude/sonnet/opus uses Anthropic;
  switching to gpt/o1/o3 uses OpenAI — auto-detected from the model name
```

**US-5: Organise Chats in Folders**
```gherkin
As a user
I want to create folders and group conversations
So that I can keep related chats together

Acceptance Criteria:
- "New Folder" creates a folder in the sidebar
- "New Chat" creates a fresh conversation
- Selecting a chat in the sidebar loads its history into the chat area
- The sidebar has a search box that filters folders by name
```

**US-6: Side Notes Panel**
```gherkin
As a user
I want a free-text scratchpad next to the chat
So that I can jot things down without leaving the conversation

Acceptance Criteria:
- A "Notes" panel sits on the right of the chat
- Text I type is preserved while I navigate within the app session
- (Persistence across reloads is NOT implemented yet — see §16)
```

---

## 2. User Interface Specification

### 2.1 Application Layout

The app is a three-pane horizontal layout (`pages/main.py:main_page()`):

```
┌────────────────┬────────────────────────────────────┬───────────────┐
│   sidebar()    │            chat_area()             │ notes_panel() │
│ (workspace/ui) │           (chat/ui.py)             │ (kb/ui.py)    │
│                │                                    │               │
│  Search        │  Header + global search            │  Header       │
│  Folders/Chats │  Message history (scroll)          │  Free-text    │
│  Footer        │  Input bar + popovers              │  textarea     │
└────────────────┴────────────────────────────────────┴───────────────┘
```

### 2.2 Chat Area Layout

```
┌─────────────────────────────────────────────┐
│  [Search] Global Search Bar                 │  ← chat_header() + global_search()
├─────────────────────────────────────────────┤
│  📝 Current Chat Title         [⋮] Actions  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────┐          │
│  │ User Message Bubble          │ [Avatar] │  ← message_bubble(role="user")
│  │ "What is ESP32?"             │          │
│  │                         6:15 PM          │
│  └──────────────────────────────┘          │
│                                             │
│  [AI]  ┌────────────────────────────────┐  │  ← message_bubble(role="assistant")
│        │ ESP32 is a low-cost, low-power │  │     Markdown + Shiki code blocks
│        │ microcontroller…               │  │
│        │                    6:15 PM      │  │
│        └────────────────────────────────┘  │
│                                             │
│  [AI]  ┌────────────────────────────────┐  │  ← while streaming:
│        │ Let me explain ▊               │  │     content updates in 40-char
│        └────────────────────────────────┘  │     batches; unclosed code
│                                             │     fences are auto-closed by
│                                             │     `_close_open_code_block`
├─────────────────────────────────────────────┤
│  [📎] [Model ▼] [🧠 ▼] [🌡 ▼] [Type…] [→] │  ← chat_input()
└─────────────────────────────────────────────┘
```

### 2.3 Component Map (as-built)

All chat components live in `mychat_reflex/features/chat/ui.py`. Shared building blocks come from `mychat_reflex/ui/primitives.py`.

| Component | File | Purpose |
|---|---|---|
| `chat_area()` | `chat/ui.py` | Top-level container: header → history → input |
| `chat_header()` | `chat/ui.py` | Title row + actions |
| `global_search()` | `chat/ui.py` | Top search bar (placeholder for future global search) |
| `chat_history()` | `chat/ui.py` | `rx.foreach(ChatState.messages, message_bubble)` |
| `message_bubble(message, index)` | `chat/ui.py` | One message; user vs assistant styling |
| `message_actions(message_id)` | `chat/ui.py` | Hover actions: copy / regenerate / delete |
| `_message_markdown(content, is_streaming)` | `chat/ui.py` | Markdown renderer w/ Shiki code blocks; faster fallback while streaming |
| `_shiki_code_block` / `_fast_code_block` | `chat/ui.py` | Two code-block renderers (high-quality vs fast) |
| `chat_input()` | `chat/ui.py` | Input field + left/right toolbars |
| `_input_left()` / `_input_right()` | `chat/ui.py` | Toolbar groups |
| `model_selector()` | `chat/ui.py` | Popover model picker |
| `thinking_selector()` | `chat/ui.py` | Popover for extended-thinking toggle + budget |
| `temperature_selector()` | `chat/ui.py` | Popover temperature picker |
| `pill_btn`, `icon_btn`, `popover`, … | `ui/primitives.py` | Cross-cutting primitives |

> **Out of scope of this spec**: sidebar (`features/workspace/ui.py`) and notes panel (`features/knowledge_base/ui.py`). They are summarised in the architecture doc and bind to `ChatState` / `KnowledgeBaseState` respectively.

---

## 3. Functional Requirements

### 3.1 Message Sending Flow (high level)

**Pre-conditions**
- A current conversation exists (`ChatState.current_conversation_id` is set; default is `"default-chat"` until the user creates one).
- An LLM service is registered in `AppContainer` (done at startup by `mychat_reflex.py:initialize_dependencies()`).
- The user has typed non-empty text in the input field and is not already generating.

**Flow**
1. User clicks Send / presses Enter → `ChatState.handle_send_message()` (a `@rx.event(background=True)` handler).
2. **Guard**: empty/whitespace prompt or `is_generating == True` → return.
3. **Optimistic UI update + persistence of user turn**:
   - Clear `input_text`, set `is_generating = True`.
   - Build a `Message(role="user", …)` with a fresh UUID and the user's avatar URL.
   - Persist it inside a short `rx.session()`.
   - Append to `self.messages`.
4. **Assistant placeholder**: append a second `Message(role="assistant", content="")` to `self.messages` so the bubble appears immediately.
5. **Resolve adapter**:
   - Read `selected_model` (string) from LocalStorage.
   - Call `_ensure_correct_adapter(model)` — re-registers an `AnthropicAdapter` or `OpenAIAdapter` in `AppContainer` if the model family changed.
   - `llm = AppContainer.resolve_llm_service()`.
6. **Stream**: instantiate `SendMessageUseCase(llm)` and iterate `use_case.execute(conversation_id, prompt, history=self.messages[:-2], config=…)`.
7. **Buffered UI updates**: a 40-character buffer batches chunks before mutating `self.messages[-1].content` inside `async with self:`; `_close_open_code_block()` keeps Markdown valid mid-stream; `await asyncio.sleep(0.01)` lets the WebSocket flush.
8. **Persist final assistant turn**:
   - Open a new `rx.session()`.
   - Insert the final `Message(role="assistant", content=full_response)`.
   - Bump `Conversation.updated_at` for the current conversation.
   - Commit.
9. Strip the safety closing-fence from `self.messages[-1].content` and set `is_generating = False`.

**Post-conditions**
- One user message and one assistant message persisted to `message`.
- `conversation.updated_at` bumped.
- Both messages visible in UI; input field empty and re-enabled.

### 3.2 Error Handling (current behaviour vs. intended)

**Current behaviour**: `handle_send_message` does **not** wrap the streaming loop in `try/except`. A failure mid-stream surfaces as a Reflex runtime error and `is_generating` may stick.

**Intended behaviour** (planned — see §16):

| Scenario | Expected user-visible behaviour |
|---|---|
| LLM API error (e.g. 401, 5xx) | Replace placeholder content with `❌ Error: <message>`; persist as a system message; reset `is_generating`. |
| Network timeout | Same as above with `⏱️ Request timed out`; offer a Retry action. |
| Invalid API key at startup | `mychat_reflex.py` logs an error; UI still loads; the first send produces an LLM error. |
| Empty / whitespace input | Silently ignored by the send guard. |
| Re-entrant send (already generating) | Silently ignored by the send guard. |

### 3.3 Streaming Buffering Pattern

The chunk loop in `ChatState.handle_send_message`:

```
chunk arrives ─▶ append to char_buffer + full_response
                 │
                 ├─ if len(char_buffer) >= 40:
                 │     async with self:
                 │         self.messages[-1].content =
                 │             _close_open_code_block(full_response)
                 │         self.messages = self.messages
                 │     yield
                 │     await asyncio.sleep(0.01)
                 │     char_buffer = ""
                 │
                 └─ when stream ends, flush remaining char_buffer the same way
```

**Why 40?** Empirically tuned to balance perceived smoothness vs. WebSocket / React-render thrash. Tunable in code.

**Why `_close_open_code_block`?** Mid-stream, an unclosed ```` ``` ```` would cause `react-markdown` to interpret following `# …` lines as headings. Appending a synthetic closing fence keeps the renderer happy; it's stripped at the end.

### 3.4 Conversation Memory

`SendMessageUseCase` rebuilds a flat transcript from `history` on every turn:

```
User: [prior turn 1]

Assistant: [prior reply 1]

User: [prior turn 2]

Assistant: [prior reply 2]

User: [current message]

Assistant:
```

This means the LLM has full context within a conversation. Implications:

- Token cost grows linearly with conversation length.
- There is no truncation / summarisation strategy yet — long chats will eventually exceed the model's context window. Tracked in §16.
- Switching models mid-conversation works, but each provider sees the same flat transcript (we do not use Anthropic/OpenAI native message arrays — by design, for adapter symmetry).

### 3.5 New Chat / New Folder

- `ChatState.create_new_chat()` — generates a UUID, persists a `Conversation(title="New Chat")`, appends to `self.chats`, sets it as the current conversation, clears `messages`.
- `ChatState.create_new_folder()` — same shape for `ChatFolder(name="New Folder")`. Renaming folders/chats is **not yet implemented**.

### 3.6 Selecting a Conversation

- `ChatState.select_chat(chat_id)` — updates `current_conversation_id`, sets `current_chat_title` from the in-memory `chats` list, then runs `LoadHistoryUseCase` inside a short `rx.session()` and replaces `self.messages`.

### 3.7 Deleting a Message

- `ChatState.delete_message(message_id)` — deletes from `message` table and removes from `self.messages`. Does **not** update `conversation.updated_at`. Hard delete (no soft-delete column today).

### 3.8 Copy / Regenerate (placeholders)

`copy_message` and `regenerate_message` exist as `pass` stubs in `ChatState`. UI hooks point at them; behaviour is a no-op. Tracked in §16.

---

## 4. Non-Functional Requirements

### 4.1 Performance
- First-chunk latency: dominated by LLM TTFC; the app adds < 5 ms before yielding the first frame.
- Per-frame WebSocket update: ~40 chars + 10 ms sleep ⇒ ~25 frames/s steady-state.
- DB writes: two short `rx.session()` blocks per turn, each typically < 5 ms on local SQLite.
- History load: single `select(Message)` ordered by `created_at` — fine up to a few hundred messages; pagination is future work.

### 4.2 Scalability
- SQLite is the dev/MVP backend. The architecture is portable to Postgres without code changes (just `db_url`).
- `ChatState.messages` holds the full conversation in memory; not suitable for tens of thousands of messages without pagination.

### 4.3 Reliability
- All committed messages are durable (SQLite WAL).
- Mid-stream failures are not yet recovered cleanly (see §3.2).

### 4.4 Usability
- Desktop-first layout (sidebar + chat + notes). Mobile is unaddressed.
- Keyboard: Enter sends. Shift+Enter newline and Esc-to-cancel are not implemented.
- Markdown + Shiki code blocks render in dark and light themes (`code_theme`, `light_code_theme` LocalStorage prefs).

---

## 5. Data Requirements

### 5.1 Message Data Model
See [`doc/3-reference/database-schema.md`](../3-reference/database-schema.md) for full schema.

**Key fields** (`features/chat/models.py`):
- `id` — UUID4 string, PK
- `conversation_id` — FK to `conversation.id`
- `role` — `"user" | "assistant" | "system"` (validated in app, no DB CHECK)
- `content` — string; rendered as Markdown + Shiki by the UI
- `created_at` — timezone-aware UTC, `default_factory`
- `model_used` — set on assistant messages
- `avatar_url` — set on user messages

### 5.2 Conversation Data Model
- `id` — UUID4 string, PK
- `title` — display name (default `"New Chat"`; auto-titling from first message is future work)
- `folder_id` — nullable FK to `chatfolder.id`
- `created_at`, `updated_at` — timezone-aware UTC

### 5.3 ChatFolder Data Model
Lives in `features/chat/models.py` today (not `features/workspace/models.py`):
- `id`, `name`, `created_at`

---

## 6. Dependencies

### 6.1 Technical Dependencies
- **Reflex** — UI framework, state, WebSocket runtime, `rx.Model` ORM wrapper.
- **SQLModel + SQLAlchemy** — under the hood for `rx.Model`.
- **Alembic** — migrations (`alembic/versions/da92f255a8fe_.py` is the current baseline).
- **anthropic** — Async SDK; lazy-imported in `infrastructure/llm_adapters.py`.
- **openai** — Async SDK; lazy-imported in `infrastructure/llm_adapters.py`.
- **python-dotenv** — `.env` loading at the Composition Root.
- **SQLite** — local DB (`reflex.db`).

### 6.2 Feature Dependencies
- **Workspace UI** (`features/workspace/ui.py`) for navigation — binds to `ChatState`.
- **Core ports** (`core/llm_ports.py`) + **DI** (`core/di.py`) for adapter abstraction.
- **Composition Root** (`mychat_reflex/mychat_reflex.py`) for adapter wiring.

---

## 7. Acceptance Criteria (Definition of Done)

### Phase 2 — Model Migration ✅ DONE
- [x] `Message`, `Conversation`, `ChatFolder` defined as `rx.Model`.
- [x] Alembic baseline migration applied (`da92f255a8fe`).
- [x] CRUD wired through `ChatState`.

### Phase 3 — Use Cases ✅ DONE
- [x] `SendMessageUseCase` implemented with `history` parameter and transcript building.
- [x] `LoadHistoryUseCase` implemented with injected `Session`.
- [x] Use cases tested with `FakeLLMAdapter` and in-memory SQLite.

### Phase 4 — State & UI ✅ DONE
- [x] `ChatState.handle_send_message` (background event handler) implemented.
- [x] Reactivity working (`async with self:` + `self.messages = self.messages`).
- [x] `rx.session()` lifetime safety verified (no session held across `await`).
- [x] LocalStorage prefs (model, temperature, reasoning, themes) working with string-only storage + computed-var converters.

### Phase 5 — Integration ✅ DONE
- [x] End-to-end: type → stream → persist → reload survives.
- [x] Streaming visible in real time with 40-char buffering.
- [x] Markdown + Shiki render correctly mid-stream (`_close_open_code_block`).

### Phase 6 — Polish 🟡 IN PROGRESS
- [x] Avatars for user messages (`pravatar.cc`).
- [x] Timestamps render via `Message.timestamp_formatted`.
- [x] Loading state via `is_generating`.
- [ ] Copy / regenerate buttons functional (currently `pass` stubs).
- [ ] Robust error handling (try/except around streaming).
- [ ] Auto-title from first user message.
- [ ] Conversation rename / delete.

---

## 8. Open Questions

- **Markdown rendering** — ✅ implemented (Shiki). Light/dark theme switching uses two LocalStorage keys.
- **Message editing** — Not in MVP. Future feature.
- **Conversation branching** — Not in MVP. Would require `parent_message_id` on `Message`.
- **Maximum conversation length** — No hard cap. Soft target: ~1000 messages before considering pagination/archiving.
- **Multi-user / auth** — Not implemented. Would require a `user_id` FK and login flow.

---

## 9. Detailed Flow Specifications

### 9.1 Message Sending Flow (Detailed)

**Pre-conditions**
- Database accessible (`reflex.db` exists, migrations applied).
- An LLM service is registered in `AppContainer`.
- A conversation is selected.

**Step-by-step** (matches `ChatState.handle_send_message` exactly):

| # | Actor | Action | Expected Behaviour | State changes |
|---|---|---|---|---|
| 1 | User | Types in input | Text appears | `input_text` updated via `set_input_text` |
| 2 | User | Clicks Send / Enter | Handler triggered | `handle_send_message()` runs (background) |
| 3 | Guard | Validate prompt | Empty / re-entrant ⇒ early return | none |
| 4 | State | Persist user msg | INSERT into `message` | `messages.append(user_msg)`, `is_generating=True`, `input_text=""` |
| 5 | State | Append empty assistant placeholder | UI shows empty bubble | `messages.append(ai_msg_placeholder)` |
| 6 | State | `_ensure_correct_adapter(model)` | Re-register adapter if model family changed | `AppContainer._llm_service` may be replaced |
| 7 | State | Resolve adapter, build `LLMConfig` | — | reads `temperature_float`, `enable_reasoning_bool`, `reasoning_budget_int` |
| 8 | UseCase | Build transcript from `history`, call `llm.generate_stream` | First chunks arrive | none |
| 9 | State | 40-char buffered updates | UI streams | `messages[-1].content = _close_open_code_block(full_response)` |
| 10 | State | Stream completes | Final flush | — |
| 11 | State | Persist final assistant message + bump `updated_at` | INSERT + UPDATE | DB row created; `conversation.updated_at` bumped |
| 12 | State | Strip safety fence, clear `is_generating` | UI re-enables send | `is_generating=False` |

**Edge cases** that are handled today:

| Scenario | Behaviour |
|---|---|
| Empty / whitespace input | Silently no-op |
| Already generating | Silently no-op |
| Pressing Enter vs clicking Send | Identical (both call `handle_send_message`) |
| Switching models mid-conversation | Adapter is swapped; transcript is rebuilt by `SendMessageUseCase` and sent to the new adapter |

**Edge cases NOT handled** (see §16):

| Scenario | Current behaviour |
|---|---|
| LLM API error mid-stream | Reflex runtime exception; `is_generating` may stick |
| Network timeout | Same as above |
| Browser closes mid-stream | Partial assistant content is lost (the final INSERT never happens) |
| Sending while DB is locked | Exception propagates |

### 9.2 Conversation Loading Flow

**Trigger**: user clicks a chat in the sidebar; `chat_item` calls `ChatState.select_chat(chat_id)`.

```
select_chat(chat_id):
  current_conversation_id = chat_id
  current_chat_title = lookup in self.chats
  with rx.session() as s:
      msgs = LoadHistoryUseCase().execute(s, chat_id)
      self.messages = [Message(**m.model_dump()) for m in msgs]
```

> **Why `Message(**m.model_dump())`?** SQLModel rows returned from a session are still attached to it. Cloning into pure in-memory objects detaches them so Reflex can serialise the list to the browser without lazy-load surprises after the session closes.

### 9.3 Real-time Streaming UX

```
Time    LLM Output             UI Display (40-char batched)
-----   -----------            ----------------------------
0.0s    (connection opens)     empty assistant bubble
0.3s    "Hello there! How c"   "Hello there! How c"  (first 40-char flush)
0.6s    "an I help you today"  "Hello there! How can I help you today"
…       …                      …
```

Until the first 40-char threshold is reached, the bubble may stay empty for a few hundred ms — perceived as "thinking". A dedicated thinking indicator is future work.

### 9.4 Error Recovery (intended design)

```
User sends
  ↓
User msg saved ✅ (committed)
  ↓
Assistant placeholder appended
  ↓
llm.generate_stream raises (e.g. 401)
  ↓
catch in handle_send_message:
  ↓
self.messages[-1].content = "❌ Error: <message>"
  ↓
persist as system message  (audit trail)
  ↓
is_generating = False
```

Not yet implemented — see §16.

---

## 10. Interaction Patterns

### 10.1 Keyboard Shortcuts

| Shortcut | Action | Status |
|---|---|---|
| Enter | Send message | ✅ Implemented |
| Shift+Enter | Newline in input | ❌ Not implemented |
| Esc | Cancel streaming | ❌ Not implemented |
| Cmd/Ctrl+C on bubble | Copy message | ❌ Not implemented (`copy_message` is a stub) |
| Up arrow on empty input | Edit last message | ❌ Future |

### 10.2 Mouse Interactions

| Action | Target | Status |
|---|---|---|
| Click | Send button | ✅ |
| Click | Sidebar chat item | ✅ → `select_chat` |
| Click | "+ Chat" / "+ Folder" | ✅ → `create_new_chat` / `create_new_folder` |
| Hover | Message bubble | ✅ shows `message_actions` |
| Click | Copy / regenerate / delete in `message_actions` | 🟡 only delete works; copy/regenerate are stubs |
| Click | Model / thinking / temperature pills | ✅ opens popovers |

### 10.3 Touch Interactions

Mobile is not in scope for the current phase.

---

## 11. Visual Design Specifications

### 11.1 Message Bubbles

Styling lives in `features/chat/ui.py` and CSS classes referenced from `assets/`. Conceptually:

- **User bubble**: right-aligned, accent-colour gradient, avatar to the right (`https://i.pravatar.cc/150?img=11`).
- **Assistant bubble**: left-aligned, neutral surface, AI icon to the left, Markdown body with Shiki code blocks.
- **Streaming**: same as assistant bubble; a synthetic closing fence may be present until the stream ends.

### 11.2 Code Themes (LocalStorage)

| Pref | Default |
|---|---|
| `code_theme` (dark) | `"nord"` |
| `light_code_theme` | `"github-light"` |

Both are stored as **strings** in LocalStorage and read directly by Shiki. See [`doc/guides/reflex-localstorage-best-practices.md`](../guides/reflex-localstorage-best-practices.md).

### 11.3 Typography & Spacing

The Reflex theme is configured at the app level in `mychat_reflex.py`:

```python
rx.theme(
    appearance="inherit",
    has_background=False,
    radius="large",
    accent_color="indigo",
)
```

Fine-grained typography is delegated to the theme + global stylesheet (`/styles.css`).

### 11.4 Loading States

- While `is_generating == True`: send button disabled, input may stay enabled (not strictly disabled today).
- A dedicated "thinking" indicator before the first chunk is **not** implemented.

---

## 12. Accessibility (target: WCAG 2.1 AA)

This is **aspirational** — the current build has not been audited.

- Screen-reader labels on input, send, and popovers.
- Visible focus rings on every interactive element.
- Sufficient contrast in both light and dark themes.
- `prefers-reduced-motion` respected (streaming animation may need throttling).

Tracked in §16.

---

## 13. Analytics & Monitoring

Not implemented. The codebase emits structured logs (see `mychat_reflex.py` logging config + the verbose info logs in `ChatState`, `SendMessageUseCase`, `AnthropicAdapter`) but does not ship to any aggregator.

Future metrics to track:
- Messages per session, conversation length distribution.
- LLM TTFC (time to first chunk), throughput, error rate.
- DB write latency.

---

## 14. Localisation

Not implemented. UI strings are hard-coded in English. When localising, externalise strings from `features/chat/ui.py`, `features/workspace/ui.py`, and `features/knowledge_base/ui.py`.

---

## 15. Testing Scenarios (BDD)

These scenarios reflect the **current** behaviour (✅ already implemented) and the **intended** error-handling layer (🟡 future).

### Scenario 1: Happy Path ✅
```gherkin
Feature: Chat Conversation

  Scenario: User sends a message and receives an AI response
    Given a conversation is selected
    And the input field is empty
    When I type "What is Reflex?"
    And I press Enter
    Then the input field is cleared
    And my message appears in the chat history
    And an empty assistant bubble appears
    And the assistant bubble fills in 40-character batches
    And the send button is disabled while streaming
    And when streaming completes
    Then the send button is re-enabled
    And both messages are persisted to the `message` table
    And `conversation.updated_at` is bumped
```

### Scenario 2: Re-entrancy Guard ✅
```gherkin
  Scenario: Sending while already generating is ignored
    Given a streaming response is in progress
    When I type something and press Enter again
    Then nothing happens (the second send is silently dropped)
```

### Scenario 3: Conversation Memory ✅
```gherkin
  Scenario: The model remembers prior turns
    Given a conversation with two prior turns
    When I send "And what about its WiFi support?"
    Then the transcript sent to the LLM contains both prior turns
    And the AI's reply references the earlier topic correctly
```

### Scenario 4: Model Switching ✅
```gherkin
  Scenario: Switching from Claude to GPT mid-conversation
    Given the model selector shows "Claude Sonnet 4.5"
    When I switch to "GPT-4o"
    And I send a new message
    Then `_ensure_correct_adapter` registers an OpenAIAdapter
    And the next reply comes from the OpenAI API
```

### Scenario 5: LocalStorage Persistence ✅
```gherkin
  Scenario: Preferences survive a page reload
    Given I set temperature to 0.3 and code theme to "dracula"
    When I refresh the page
    Then temperature is still 0.3
    And the code theme is still "dracula"
    And both values are still stored as strings in LocalStorage
```

### Scenario 6: API Error 🟡 (intended)
```gherkin
  Scenario: LLM API returns an error
    Given the Anthropic API key is invalid
    When I send a message
    Then my user message is persisted
    And the assistant bubble shows "❌ Error: …"
    And `is_generating` is reset to False
    And I can send another message
```

### Scenario 7: Network Timeout 🟡 (intended)
```gherkin
  Scenario: Request times out
    Given the network drops mid-stream
    When 30s pass with no chunk
    Then the assistant bubble shows "⏱️ Request timed out"
    And a Retry action is offered
```

---

## 16. Known Gaps / Future Work

This section is the canonical "what's missing" list for the chat feature. Items echo §15 of the architecture doc where they overlap.

### 16.1 Robustness
- [ ] Wrap `handle_send_message` streaming loop in `try/except`; persist failures as system messages.
- [ ] Handle browser-close-mid-stream (resume or mark message as `[interrupted]`).
- [ ] Cancel-in-flight (`Esc` key + AbortController on the LLM client).

### 16.2 UX polish
- [ ] `copy_message` and `regenerate_message` (currently `pass` stubs).
- [ ] Conversation rename / delete.
- [ ] Auto-title conversation from the first user message.
- [ ] Shift+Enter for newline.
- [ ] "Thinking…" indicator before the first chunk arrives.
- [ ] Auto-scroll behaviour: stop on user scroll-up, resume on send.

### 16.3 Scaling
- [ ] Paginate `LoadHistoryUseCase` (load tail; lazy-load older on scroll-up).
- [ ] Add `(conversation_id, created_at)` composite index (see DB schema doc §9.1).
- [ ] Token-aware history truncation / summarisation for long conversations.

### 16.4 Knowledge Base
- [ ] Persist notes to a `Note` model (currently in-memory only).
- [ ] Per-conversation notes vs global notes — product decision needed.

### 16.5 Workspace state extraction
- [ ] Extract folder/chat list state from `ChatState` into a dedicated `WorkspaceState`.
- [ ] Move `ChatFolder` from `features/chat/models.py` to `features/workspace/models.py`.

### 16.6 Accessibility
- [ ] WCAG 2.1 AA audit.
- [ ] Keyboard navigation pass.
- [ ] `prefers-reduced-motion` support.

### 16.7 Cleanup
- [ ] Delete the orphan `tests/test_send_message_use_case.py` (duplicates `tests/features/chat/test_use_cases.py` and contains 5 redundant import lines).

---

## 17. Roll-out Plan

### Phase 1 — MVP ✅
- Text-only messages
- Anthropic + OpenAI adapters with auto-detection
- Streaming with 40-char buffering
- Basic create/select/delete

### Phase 2 — Polish 🟡 (current)
- Robust error handling
- Copy / regenerate / rename
- Auto-title
- "Thinking" indicator

### Phase 3 — Advanced
- History pagination + summarisation
- Conversation branching (`parent_message_id`)
- Message editing
- Mobile layout

### Phase 4 — Persistence depth
- Knowledge Base persistence
- Export / import (JSON, Markdown)
- Search across conversations

### Phase 5 — Multi-user
- Authentication
- Per-user isolation (`user_id` FK)
- Conversation sharing
