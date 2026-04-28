# GUI Wiring Architecture Diagram

## Component Interaction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (React)                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Model Popup  │  │ Think Popup  │  │ Temp Popup   │          │
│  │ - Sonnet 4.5 │  │ - Toggle     │  │ - Slider     │          │
│  │ - GPT-4o     │  │ - Budget     │  │ - Presets    │          │
│  │ - o1         │  │              │  │              │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                  │
│                            │                                     │
│                    WebSocket Events                              │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ChatState (ViewModel)                         │
├─────────────────────────────────────────────────────────────────┤
│  State Variables:                                                │
│  • selected_model: str           (LocalStorage)                  │
│  • temperature: float            (LocalStorage)                  │
│  • enable_reasoning: bool        (LocalStorage)                  │
│  • reasoning_budget: int         (LocalStorage)                  │
│                                                                   │
│  Event Handlers:                                                 │
│  • set_selected_model(model) ──► _ensure_correct_adapter()      │
│  • set_temperature(value)                                        │
│  • set_enable_reasoning(bool)                                    │
│  • set_reasoning_budget(int)                                     │
│                                                                   │
│  Computed Properties:                                            │
│  • model_display_name() → "Claude Sonnet 4.5"                   │
│  • reasoning_effort_display() → "Medium"                         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ Calls on send_message
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│            _ensure_correct_adapter(model: str)                   │
├─────────────────────────────────────────────────────────────────┤
│  if model starts with "claude":                                  │
│      adapter = AnthropicAdapter(api_key, model)                  │
│  elif model starts with "gpt" or "o1":                           │
│      adapter = OpenAIAdapter(api_key, model)                     │
│                                                                   │
│  AppContainer.register_llm_service(adapter)                      │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ Dependency Injection
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AppContainer                                │
│                   (Service Locator)                              │
├─────────────────────────────────────────────────────────────────┤
│  _llm_service: ILLMService                                       │
│                                                                   │
│  ┌────────────────┐              ┌────────────────┐             │
│  │ Anthropic      │              │ OpenAI         │             │
│  │ Adapter        │ ◄────OR────► │ Adapter        │             │
│  └────────────────┘              └────────────────┘             │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ resolve_llm_service()
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SendMessageUseCase                              │
├─────────────────────────────────────────────────────────────────┤
│  execute(                                                        │
│      user_message: str,                                          │
│      config: LLMConfig(                                          │
│          temperature=0.7,                                        │
│          enable_reasoning=True,                                  │
│          reasoning_budget=8000                                   │
│      )                                                           │
│  )                                                               │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ Calls interface method
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              ILLMService.generate_stream()                       │
├─────────────────────────────────────────────────────────────────┤
│  Implemented by:                                                 │
│                                                                   │
│  AnthropicAdapter               OpenAIAdapter                    │
│  ─────────────────              ─────────────                    │
│  • Maps to thinking{}           • Maps to reasoning_effort       │
│  • Forces temp=1.0 if thinking  • Strips temp if o1 model        │
│  • Uses AsyncAnthropic client   • Uses AsyncOpenAI client        │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ Async Generator
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External LLM API                              │
│               (Anthropic / OpenAI / etc.)                        │
└─────────────────────────────────────────────────────────────────┘
```

## State Flow Diagram

```
User Clicks Model Selector
         │
         ▼
set_selected_model("gpt-4o")
         │
         ▼
Update state.selected_model ──► LocalStorage persists
         │
         ▼
[User clicks Send Message]
         │
         ▼
handle_send_message() reads:
  - selected_model
  - temperature
  - enable_reasoning
  - reasoning_budget
         │
         ▼
_ensure_correct_adapter("gpt-4o")
         │
         ├─► Current adapter model = "gpt-4o"?
         │   YES → Skip (already correct)
         │   NO  → Continue
         ▼
Create OpenAIAdapter("gpt-4o")
         │
         ▼
AppContainer.register_llm_service(adapter)
         │
         ▼
SendMessageUseCase.execute(
    config=LLMConfig(
        temperature=0.7,
        enable_reasoning=False
    )
)
         │
         ▼
llm_service = AppContainer.resolve_llm_service()
         │
         ▼
llm_service.generate_stream(prompt, config)
         │
         ▼
Stream response chunks back to ChatState
         │
         ▼
Update UI via WebSocket
```

## Key Architectural Decisions

### 1. LocalStorage Persistence
All user preferences (model, temperature, reasoning) are stored in browser LocalStorage:
- Survives page refreshes
- Per-browser storage (not per-user)
- No database writes needed for UI preferences

### 2. Dynamic Adapter Switching
Instead of requiring app restart to change models:
- Adapter is re-instantiated on model change
- Service Locator pattern allows runtime replacement
- Old adapter is garbage collected

### 3. Generic Domain Config
`LLMConfig` remains provider-agnostic:
```python
LLMConfig(
    temperature=0.7,
    enable_reasoning=True,
    reasoning_budget=8000
)
```

Each adapter translates to provider-specific format:
- **Anthropic**: `thinking: {type: "enabled", budget_tokens: 8000}`
- **OpenAI**: `reasoning_effort: "medium"`

### 4. UI State Separation
Following MVVM:
- **View** (`ui.py`): Pure presentation, no logic
- **ViewModel** (`ChatState`): UI state + event handlers
- **Model** (`SendMessageUseCase`): Business logic

### 5. Computed Properties for Display
Instead of storing both ID and display name:
```python
@rx.var
def model_display_name(self) -> str:
    return {"claude-sonnet-4-5": "Claude Sonnet 4.5"}[self.selected_model]
```

Benefits:
- Single source of truth (state only stores ID)
- Display logic centralized
- Easy to update UI labels without migration

## Data Flow Summary

1. **User Interaction** → Popover click → `set_*()` handler
2. **State Update** → LocalStorage persist → WebSocket sync to browser
3. **Message Send** → Read current config → Ensure adapter matches
4. **Adapter Switch** (if needed) → DI container update
5. **Use Case Call** → Generic `LLMConfig` passed in
6. **Adapter Translation** → Provider-specific JSON payload
7. **Streaming** → Chunks → State buffer → WebSocket → React render

## Testing Touch Points

### Unit Tests
- [ ] `set_selected_model()` updates state
- [ ] `model_display_name()` returns correct mapping
- [ ] `_ensure_correct_adapter()` creates correct adapter type
- [ ] `reasoning_effort_display()` matches budget ranges

### Integration Tests
- [ ] Switching from Anthropic to OpenAI model persists
- [ ] Temperature setting passed to adapter
- [ ] Reasoning config correctly translated for each provider

### E2E Tests
- [ ] Model selector popover opens/closes
- [ ] Selected model highlighted in UI
- [ ] Message generates with new model after switching
- [ ] LocalStorage survives page refresh
