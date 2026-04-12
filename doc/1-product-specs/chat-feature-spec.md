# Product Specification: Chat Feature

**Feature**: Core AI Chat Conversation
**Status**: Active Development (Phase 2 - Model Migration)
**Priority**: P0 (Critical Path)
**Last Updated**: 2026-04-12

---

## 1. Feature Overview

### 1.1 Business Value
Enable users to have real-time conversations with AI assistants (Claude/GPT) using a ChatGPT-like interface with streaming responses.

### 1.2 User Stories

**US-1: Send Message to AI**
```gherkin
As a user
I want to send a message to the AI assistant
So that I can get intelligent responses to my questions

Acceptance Criteria:
- User can type message in input field
- User can press Enter or click Send button to submit
- Message appears in chat history immediately (optimistic update)
- Input field clears after sending
- Send button is disabled while AI is generating response
```

**US-2: Receive Streaming AI Response**
```gherkin
As a user
I want to see the AI response appear word-by-word in real-time
So that I know the system is working and can start reading early

Acceptance Criteria:
- AI response appears as a new message bubble below user message
- Text streams in word-by-word (not all at once)
- Loading indicator shows while AI is thinking
- User can see typing animation or progress indicator
- Response completes and becomes static when done
```

**US-3: View Conversation History**
```gherkin
As a user
I want to see all previous messages in the current conversation
So that I can review the context and previous answers

Acceptance Criteria:
- Messages are displayed in chronological order (oldest at top)
- User messages appear on right with avatar
- AI messages appear on left with AI icon
- Timestamps are shown for each message
- Conversation persists across page refreshes
```

---

## 2. User Interface Specification

### 2.1 Chat Area Layout

```
┌─────────────────────────────────────────────┐
│  [Search] Global Search Bar                 │
├─────────────────────────────────────────────┤
│  📝 ESP32 Overview            [⋮] Actions   │  ← Chat Header
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────┐          │
│  │ User Message Bubble          │ [Avatar] │  ← User Message
│  │ "What is ESP32?"             │          │
│  │                         6:15 PM          │
│  └──────────────────────────────┘          │
│                                             │
│  [AI]  ┌────────────────────────────────┐  │  ← AI Message
│        │ ESP32 is a low-cost, low-power │  │
│        │ microcontroller with built-in  │  │
│        │ Wi-Fi and Bluetooth...         │  │
│        │                    6:15 PM      │  │
│        └────────────────────────────────┘  │
│                                             │
│  (More messages...)                         │
│                                             │
│  [AI]  ┌────────────────────────────────┐  │  ← Streaming
│        │ Let me explain ▊               │  │     (Cursor)
│        └────────────────────────────────┘  │
│                                             │
├─────────────────────────────────────────────┤
│  [📎] [🎤] [Type message...] [Model ▼] [→] │  ← Input Area
└─────────────────────────────────────────────┘
```

### 2.2 Component Breakdown

**chat_area()** - Main container
- Renders header, message list, input
- Full height, scrollable

**chat_header()** - Top bar
- Shows current chat title
- Actions menu (rename, delete, etc.)

**chat_history()** - Message list
- Auto-scrolls to bottom on new messages
- Virtualized for performance (future)

**message_bubble(message: Message)** - Individual message
- User vs AI styling
- Avatar/icon
- Timestamp
- Action buttons (copy, regenerate)

**chat_input()** - Message input area
- Text input field
- Send button
- Model selector dropdown
- Attachment buttons (future)

---

## 3. Functional Requirements

### 3.1 Message Sending Flow

**Pre-conditions**:
- User is viewing a conversation
- User has typed text in input field

**Flow**:
1. User clicks Send or presses Enter
2. **Optimistic UI Update**:
   - Clear input field immediately
   - Create user message bubble with current text
   - Append to chat history
   - Show "generating" state (disable send button)
3. **State Management** (`ChatState.handle_send_message()`):
   - Save user message to database via `rx.session()`
   - Create empty AI message placeholder
   - Call `SendMessageUseCase.execute()`
4. **Use Case Execution** (`SendMessageUseCase`):
   - Stream from `ILLMService` (Anthropic or OpenAI)
   - Yield text chunks
5. **State Updates**:
   - Append each chunk to AI message content
   - Trigger UI reactivity with `self.messages = self.messages`
6. **Completion**:
   - Save final AI message to database
   - Set `is_generating = False`
   - Re-enable send button

**Post-conditions**:
- User message persisted in database
- AI message persisted in database
- Both messages visible in UI
- Input field is empty and enabled

### 3.2 Error Handling

**Scenario 1: LLM API Error**
- Display error message in chat: "❌ Error: Could not connect to AI service"
- Log error details to console
- Re-enable send button (allow retry)
- Do NOT save partial AI response

**Scenario 2: Network Timeout**
- Show timeout message: "⏱️ Request timed out. Please try again."
- Allow user to resend message

**Scenario 3: Invalid API Key**
- Show configuration error: "⚙️ API key not configured. Check settings."
- Link to settings page (future)

---

## 4. Non-Functional Requirements

### 4.1 Performance
- Message rendering: < 50ms per message
- Streaming chunk latency: < 100ms from LLM receipt
- Database write: < 50ms per message
- Chat history load: < 200ms for 100 messages

### 4.2 Scalability
- Support up to 1000 messages per conversation
- Support up to 100 concurrent conversations
- Handle streaming chunks at 50+ chunks/second

### 4.3 Reliability
- All messages persisted to database (no data loss)
- Graceful degradation on LLM API failures
- Auto-retry with exponential backoff (future)

### 4.4 Usability
- Responsive on desktop (1920x1080) and laptop (1366x768)
- Keyboard shortcuts (Enter to send, Shift+Enter for newline)
- Accessible (ARIA labels, keyboard navigation)

---

## 5. Data Requirements

### 5.1 Message Data Model
See `doc/3-reference/database-schema.md` for full schema.

**Key Fields**:
- `id`: Unique identifier
- `conversation_id`: Parent conversation FK
- `role`: "user" | "assistant" | "system"
- `content`: Message text
- `created_at`: Timestamp
- `model_used`: LLM model name (assistant only)

### 5.2 Conversation Data Model
**Key Fields**:
- `id`: Unique identifier
- `title`: Display name
- `folder_id`: Optional parent folder FK
- `created_at`, `updated_at`: Timestamps

---

## 6. Dependencies

### 6.1 Technical Dependencies
- Reflex framework (state management, UI)
- Anthropic SDK (`anthropic` package)
- OpenAI SDK (`openai` package)
- SQLite (via Reflex rx.Model)

### 6.2 Feature Dependencies
- **Workspace Feature** (sidebar): For chat navigation
- **Core LLM Ports**: For AI provider abstraction

---

## 7. Acceptance Criteria (Definition of Done)

### Phase 2 (Current - Model Migration)
- [x] Message rx.Model created
- [x] Conversation rx.Model created
- [ ] Models pass database migration
- [ ] Models support CRUD operations
- [ ] Models integrate with ChatState

### Phase 3 (Use Cases)
- [ ] SendMessageUseCase implemented
- [ ] Use case streams from ILLMService
- [ ] Use case tested with FakeLLM

### Phase 4 (State & UI)
- [ ] ChatState.handle_send_message() implemented
- [ ] Reflex reactivity working (message list updates)
- [ ] rx.session() safety verified (no holding during streaming)

### Phase 5 (Integration)
- [ ] End-to-end flow works (user types → AI responds)
- [ ] Messages persist across page refresh
- [ ] Streaming appears word-by-word in UI
- [ ] Error handling works for API failures

### Phase 6 (Polish)
- [ ] Timestamps display correctly
- [ ] Avatars/icons render
- [ ] Loading states show during generation
- [ ] Copy/regenerate buttons work

---

## 8. Open Questions

- Q: Should we support markdown rendering in messages?
  - A: Yes, but in Phase 6 (not MVP)

- Q: Should we support message editing?
  - A: No, not in MVP. Future feature.

- Q: Should we support conversation branching?
  - A: No, not in MVP. Future feature.

- Q: Maximum conversation length?
  - A: 1000 messages (soft limit). Archive/split in future.

---

## 9. Detailed Flow Specifications

### 9.1 Message Sending Flow (Detailed)

**Pre-conditions**:
- User is authenticated (future)
- User has selected a conversation
- Database is accessible
- LLM API key is configured

**Step-by-Step Flow**:

| Step | Actor | Action | Expected Behavior | State Changes |
|------|-------|--------|-------------------|---------------|
| 1 | User | Types "What is ESP32?" in input | Text appears in input field | `input_text = "What is ESP32?"` |
| 2 | User | Clicks Send button | Input clears, send disabled | `input_text = ""`, `is_generating = true` |
| 3 | System | Optimistic UI update | User message appears in chat | `messages.append(user_msg)` |
| 4 | System | Save user message to DB | INSERT into messages table | DB: message row created |
| 5 | System | Create AI placeholder | Empty AI bubble appears | `messages.append(ai_placeholder)` |
| 6 | ChatState | Call SendMessageUseCase | Use case starts streaming | N/A (pure function) |
| 7 | UseCase | Stream from ILLMService | Chunks start arriving | N/A |
| 8 | ChatState | Append chunks to response | AI message updates word-by-word | `messages[-1].content += chunk` |
| 9 | ChatState | Save complete AI response | UPDATE messages table | DB: AI message saved |
| 10 | System | Re-enable send button | User can send next message | `is_generating = false` |

**Post-conditions**:
- User message persisted in DB
- AI message persisted in DB
- Both visible in UI
- Input ready for next message
- Conversation `updated_at` timestamp updated

**Edge Cases**:

| Scenario | Expected Behavior |
|----------|-------------------|
| User presses Enter instead of clicking Send | Same as clicking Send button |
| User clicks Send with empty input | Nothing happens (validation) |
| User closes browser during streaming | Message partially saved, continue on reload |
| LLM API returns error | Display error message, don't save AI response |
| Database write fails | Display error, rollback transaction |
| Network timeout after 30s | Display timeout error, allow retry |

### 9.2 Conversation Loading Flow

**Trigger**: User clicks on a conversation in sidebar

**Flow**:
1. User clicks conversation item in sidebar
2. WorkspaceState updates `selected_chat_id`
3. ChatState detects change (event listener)
4. ChatState calls `LoadHistoryUseCase.execute(conversation_id)`
5. Use case queries database for messages
6. Messages loaded into `ChatState.messages`
7. UI auto-updates via reactivity
8. Chat area scrolls to bottom

**Performance Requirements**:
- Load time < 200ms for 100 messages
- Load time < 500ms for 500 messages
- Lazy loading for conversations > 500 messages

### 9.3 Real-time Streaming Flow

**Detailed Streaming Behavior**:

```
Time    LLM Output              UI Display
-----   -----------             ----------
0.0s    (connection opens)      "Thinking..." indicator
0.1s    "Hello"                 "Hello"
0.2s    " there"                "Hello there"
0.3s    "!"                     "Hello there!"
0.4s    " How"                  "Hello there! How"
0.5s    " can"                  "Hello there! How can"
...     ...                     ...
10.0s   (stream ends)           Full message + timestamp
```

**UI Feedback Patterns**:
- **0-100ms**: No visible indicator (too fast)
- **100ms-500ms**: Show "thinking" pulse animation
- **500ms+**: Show progress indicator
- **First chunk arrives**: Replace indicator with text
- **Subsequent chunks**: Append to existing text
- **Stream completes**: Add timestamp, enable actions

### 9.4 Error Recovery Flows

**Scenario 1: LLM API Error (401 Unauthorized)**

```
User sends message
  ↓
State saves user message to DB ✅
  ↓
State calls SendMessageUseCase
  ↓
UseCase calls llm.generate_stream()
  ↓
LLM returns 401 Unauthorized ❌
  ↓
UseCase raises exception
  ↓
State catches exception
  ↓
State creates error message:
  "❌ API Error: Invalid API key. Please check settings."
  ↓
State saves error message to DB (as system message)
  ↓
UI displays error in chat
  ↓
State re-enables send button
  ↓
User can retry or fix settings
```

**Scenario 2: Network Timeout**

```
User sends message
  ↓
Streaming starts... 10 seconds pass... 20 seconds... 30 seconds...
  ↓
Timeout exception raised
  ↓
State displays: "⏱️ Request timed out. Try again?"
  ↓
State shows [Retry] button
  ↓
User clicks Retry
  ↓
State re-sends last user message
  ↓
Streaming resumes (hopefully!)
```

**Scenario 3: Partial Stream Interruption**

```
Streaming: "Hello there! How can I..." (stream breaks)
  ↓
State detects stream ended prematurely
  ↓
State saves partial response with marker:
  content: "Hello there! How can I... [interrupted]"
  ↓
UI shows warning icon next to message
  ↓
User can click [Regenerate] to try again
```

---

## 10. Interaction Patterns

### 10.1 Keyboard Shortcuts

| Shortcut | Action | Context |
|----------|--------|---------|
| Enter | Send message | Input field focused |
| Shift+Enter | New line | Input field focused |
| Ctrl+C / Cmd+C | Copy message | Message hovered |
| Escape | Cancel streaming | While AI generating |
| ↑ (Up arrow) | Edit last message | Input empty (future) |

### 10.2 Mouse Interactions

| Action | Target | Behavior |
|--------|--------|----------|
| Click | Send button | Send message |
| Click | Message bubble | Select message (future) |
| Hover | Message bubble | Show action buttons (copy, regenerate) |
| Right-click | Message bubble | Context menu (future) |
| Scroll | Chat area | Auto-scroll stops when user scrolls up |

### 10.3 Touch Interactions (Mobile - Future)

| Gesture | Target | Behavior |
|---------|--------|----------|
| Tap | Send button | Send message |
| Long-press | Message | Show action menu |
| Swipe left | Message | Quick delete (future) |
| Pull-down | Chat area | Load older messages |

---

## 11. Visual Design Specifications

### 11.1 Message Bubble Styling

**User Messages**:
```css
.message-bubble-user {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 18px 18px 4px 18px;
  padding: 12px 16px;
  max-width: 70%;
  align-self: flex-end;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}
```

**AI Messages**:
```css
.message-bubble-ai {
  background: #f7f7f8;
  color: #1a1a1a;
  border-radius: 18px 18px 18px 4px;
  padding: 12px 16px;
  max-width: 80%;
  align-self: flex-start;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

### 11.2 Typography

- **Message Text**: 16px, line-height 1.5, system font stack
- **Timestamp**: 12px, gray-500, medium weight
- **Input Text**: 16px, system font stack
- **Placeholder**: 16px, gray-400

### 11.3 Spacing

- Message-to-message: 16px vertical gap
- Message bubble padding: 12px vertical, 16px horizontal
- Input area padding: 16px all sides
- Avatar-to-text gap: 12px

### 11.4 Loading States

**AI Thinking Indicator**:
```
┌────────────────────────┐
│ ● ● ●                  │  ← Animated dots
│ Claude is thinking...  │
└────────────────────────┘
```

**Streaming Indicator**:
- Blinking cursor (▊) at end of text while streaming
- Pulse animation on AI avatar

---

## 12. Accessibility Requirements (WCAG 2.1 Level AA)

### 12.1 Screen Reader Support

- All messages have `role="article"` and `aria-label="Message from {User/AI}"`
- Input field has `aria-label="Type your message"`
- Send button has `aria-label="Send message"` and `aria-disabled` when generating
- Loading states announced via `aria-live="polite"`

### 12.2 Keyboard Navigation

- Tab order: Input field → Send button → Message actions
- Focus visible indicators on all interactive elements
- Focus trap when modal/menu open (future)

### 12.3 Color Contrast

- User message text on gradient: 4.5:1 minimum
- AI message text on light background: 7:1 (AAA)
- Timestamp text: 4.5:1 minimum
- Error messages: Red with sufficient contrast

### 12.4 Motion Preferences

```css
@media (prefers-reduced-motion: reduce) {
  .typing-indicator,
  .pulse-animation {
    animation: none;
  }
}
```

---

## 13. Analytics & Monitoring

### 13.1 Key Metrics to Track

**User Engagement**:
- Messages sent per session
- Average conversation length
- Active users per day
- Retention rate (7-day, 30-day)

**Performance Metrics**:
- Message send latency (DB write time)
- LLM first-chunk-time (TTFC - Time To First Chunk)
- LLM streaming speed (chunks/second)
- Database query time (load history)

**Error Metrics**:
- LLM API error rate
- Database write failures
- Client-side errors (JavaScript exceptions)
- Timeout rate

### 13.2 Event Tracking (Future)

```python
# Example telemetry events
analytics.track("message_sent", {
    "conversation_id": conv_id,
    "message_length": len(text),
    "model_used": "claude-sonnet-4",
    "timestamp": datetime.utcnow()
})

analytics.track("streaming_started", {
    "conversation_id": conv_id,
    "model": "claude-sonnet-4"
})

analytics.track("streaming_completed", {
    "conversation_id": conv_id,
    "total_chunks": chunk_count,
    "duration_ms": duration,
    "tokens_generated": token_count
})
```

---

## 14. Localization Considerations (Future)

### 14.1 Text Strings to Externalize

```python
STRINGS = {
    "en": {
        "input_placeholder": "Type a message...",
        "send_button": "Send",
        "thinking": "Thinking...",
        "error_api": "Error: Could not connect to AI service",
        "error_timeout": "Request timed out. Try again?",
    },
    "pl": {
        "input_placeholder": "Wpisz wiadomość...",
        "send_button": "Wyślij",
        "thinking": "Myślę...",
        "error_api": "Błąd: Nie można połączyć się z AI",
        "error_timeout": "Przekroczono czas. Spróbuj ponownie?",
    }
}
```

### 14.2 Date/Time Formatting

- Use user's locale for timestamp formatting
- Support 12h/24h time formats
- Relative timestamps: "Just now", "5 minutes ago", etc.

---

## 15. Testing Scenarios (BDD Format)

### Scenario 1: Happy Path - Send and Receive Message

```gherkin
Feature: Chat Conversation
  As a user
  I want to send messages to AI
  So that I can get intelligent responses

  Scenario: User sends message and receives AI response
    Given I am viewing a conversation
    And the input field is empty
    When I type "What is Reflex framework?"
    And I click the Send button
    Then the input field should be cleared
    And my message should appear in the chat history
    And an AI message should start appearing
    And the AI response should stream word-by-word
    And the send button should be disabled
    And when streaming completes
    Then the send button should be re-enabled
    And both messages should be saved to the database
    And the conversation updated_at timestamp should be updated
```

### Scenario 2: Error Handling - API Error

```gherkin
  Scenario: LLM API returns error
    Given I am viewing a conversation
    And the Anthropic API key is invalid
    When I send a message "Hello"
    Then my message should appear in chat
    And an error message should appear
    And the error should say "API Error: Invalid API key"
    And the send button should be re-enabled
    And I should be able to send another message
    And the error should be logged for debugging
```

### Scenario 3: Network Resilience - Timeout

```gherkin
  Scenario: Request times out
    Given I am viewing a conversation
    And the network is slow
    When I send a message "Explain quantum computing"
    And 30 seconds pass with no response
    Then a timeout error should appear
    And the message should say "Request timed out"
    And a Retry button should appear
    When I click Retry
    Then the request should be sent again
```

### Scenario 4: UX - Keyboard Shortcuts

```gherkin
  Scenario: User sends message with Enter key
    Given I am viewing a conversation
    When I type "Hello" in the input field
    And I press the Enter key
    Then the message should be sent
    And the input field should be cleared

  Scenario: User adds newline with Shift+Enter
    Given I am typing a multi-line message
    When I press Shift+Enter
    Then a newline should be added to the input
    And the message should NOT be sent
```

---

## 16. Migration Checklist (From Old Architecture)

### 16.1 Code Migration

- [ ] Remove FastAPI dependencies from pyproject.toml
- [ ] Remove HTTP client code from old ChatState
- [ ] Migrate message models to rx.Model
- [ ] Migrate conversation models to rx.Model
- [ ] Migrate SendMessageUseCase (keep pure logic)
- [ ] Migrate UI components to features/chat/ui.py
- [ ] Update imports throughout codebase
- [ ] Remove src/ directory entirely

### 16.2 Data Migration

- [ ] Export existing conversations from old DB
- [ ] Run reflex db migrate to create new schema
- [ ] Import conversations into new schema
- [ ] Verify data integrity (count messages, check timestamps)
- [ ] Test conversation loading with migrated data

### 16.3 Testing Migration

- [ ] Update unit tests for use cases
- [ ] Create Reflex integration tests
- [ ] Test streaming with FakeLLM adapter
- [ ] Test database persistence
- [ ] Test UI reactivity (messages update)
- [ ] Manual QA on migrated conversations

---

## 17. Roll-out Plan

### Phase 1: MVP (Current)
- ✅ Text-only messages
- ✅ Single LLM provider (Anthropic)
- ✅ Basic streaming
- ✅ Simple error handling

### Phase 2: Enhanced UX
- [ ] Real-time streaming updates in UI
- [ ] Copy message button
- [ ] Regenerate response button
- [ ] Conversation title auto-generation
- [ ] Better error messages with retry

### Phase 3: Advanced Features
- [ ] Markdown rendering in messages
- [ ] Code syntax highlighting
- [ ] Model selector in UI (switch between Claude/GPT)
- [ ] Conversation branching
- [ ] Message editing

### Phase 4: Polish
- [ ] Animations and transitions
- [ ] Dark mode
- [ ] Mobile responsive design
- [ ] Accessibility audit
- [ ] Performance optimization (virtualized scrolling)

### Phase 5: Enterprise Features
- [ ] Multi-user support
- [ ] User authentication
- [ ] Conversation sharing
- [ ] Export to markdown/PDF
- [ ] Analytics dashboard
