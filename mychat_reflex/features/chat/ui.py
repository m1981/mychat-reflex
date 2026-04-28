"""
Chat Feature UI Components.

Contains all UI elements for the chat bounded context:
- Message bubbles
- Chat input area
- Chat history and layout
"""

import reflex as rx
from reflex.components.datadisplay.shiki_code_block import ShikiHighLevelCodeBlock

from .state import ChatState
from .models import Message


# ============================================================================
# HELPERS
# ============================================================================


LIGHT_CODE_THEMES = (
    "github-light",
    "github-light-default",
    "one-light",
    "light-plus",
    "min-light",
    "solarized-light",
    "catppuccin-latte",
    "vitesse-light",
    "snazzy-light",
)

DARK_CODE_THEMES = (
    "nord",
    "one-dark-pro",
    "dracula",
    "night-owl",
    "dark-plus",
    "github-dark",
    "github-dark-default",
    "material-theme-ocean",
    "tokyo-night",
    "catppuccin-mocha",
    "ayu-dark",
)


DYNAMIC_CODE_THEME_CONFIG = {
    "mode": "dynamic-local-storage",
    "light_storage_key": "light_code_theme_v4",
    "dark_storage_key": "code_theme_v4",
    "light_default": "github-light",
    "dark_default": "nord",
}


def _shiki_code_block(text, **props):
    """Heavy WASM-based Shiki renderer (Used for finished messages)."""
    # Reverted to props.get("language") to prevent strict Literal type crashes during compile
    language = props.get("language")
    return ShikiHighLevelCodeBlock.create(
        text,
        language=language,
        theme="nord",
        themes=DYNAMIC_CODE_THEME_CONFIG,
        show_line_numbers=False,
        wrap_long_lines=True,
        width="100%",
    )


def _fast_code_block(text, **props):
    """Fast standard renderer (Used during streaming to prevent flickering)."""
    # Using raw HTML elements prevents Reflex compiler crashes with _MOCK_ARG
    # and is extremely fast for React to render during streaming.
    return rx.el.pre(
        rx.el.code(text),
        class_name="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-x-auto my-4 text-sm font-mono text-gray-800 dark:text-gray-200",
    )


# Use "pre" as required by Reflex >= 0.8.25
STATIC_MARKDOWN_MAP = {
    "pre": _shiki_code_block,
}

STREAMING_MARKDOWN_MAP = {
    "pre": _fast_code_block,
}


def _message_markdown(content: str, is_streaming: bool) -> rx.Component:
    """Render markdown, choosing the safe renderer if currently streaming."""

    common_classes = [
        "prose max-w-none leading-relaxed",
        rx.color_mode_cond("text-[#3c4043]", "text-gray-200"),
    ]

    return rx.cond(
        is_streaming,
        # 1. Fast renderer for streaming
        rx.markdown(
            content,
            class_name=common_classes,
            component_map=STREAMING_MARKDOWN_MAP,
        ),
        # 2. Heavy Shiki renderer for finished messages
        rx.markdown(
            content,
            class_name=common_classes,
            component_map=STATIC_MARKDOWN_MAP,
        ),
    )


# ============================================================================
# MESSAGE BUBBLE COMPONENTS
# ============================================================================


def message_actions(message_id: str) -> rx.Component:
    """Action buttons for a message (copy, edit, delete, regenerate)."""
    return rx.box(
        rx.button(
            rx.icon("copy", size=14),
            on_click=lambda: ChatState.copy_message(message_id),
            variant="ghost",
            class_name="hover:text-[#202124] dark:hover:text-gray-200 cursor-pointer",
        ),
        rx.button(
            rx.icon("pencil", size=14),
            variant="ghost",
            class_name="hover:text-[#202124] dark:hover:text-gray-200 cursor-pointer",
        ),
        rx.button(
            rx.icon("trash-2", size=14),
            on_click=lambda: ChatState.delete_message(message_id),
            variant="ghost",
            class_name="hover:text-[#202124] dark:hover:text-gray-200 cursor-pointer",
        ),
        rx.button(
            rx.icon("rotate-cw", size=14),
            on_click=lambda: ChatState.regenerate_message(message_id),
            variant="ghost",
            class_name="hover:text-[#202124] dark:hover:text-gray-200 cursor-pointer",
        ),
        class_name="flex gap-3 text-[#5f6368] dark:text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity",
    )


def message_bubble(message: Message, index: int) -> rx.Component:
    """A single message bubble (user or AI)."""

    # Determine if this specific message is currently being streamed
    is_last_message = index == (ChatState.messages.length() - 1)
    is_currently_streaming = is_last_message & ChatState.is_generating

    return rx.box(
        rx.box(
            # Header with author label and timestamp
            rx.box(
                rx.text(
                    rx.cond(message.is_user, "User", "Model"),
                    class_name=[
                        "font-semibold text-sm",
                        rx.color_mode_cond("text-[#202124]", "text-gray-100"),
                    ],
                ),
                rx.text(
                    message.timestamp_formatted,
                    class_name=[
                        "text-xs ml-2",
                        rx.color_mode_cond("text-[#5f6368]", "text-gray-400"),
                    ],
                ),
                class_name="flex items-baseline mb-1",
            ),
            # Message content
            rx.box(
                _message_markdown(message.content, is_currently_streaming),
                class_name="text-[15px]",
            ),
            # Actions and run-time footer
            rx.box(
                message_actions(message.id),
                rx.cond(
                    ~message.is_user,
                    rx.text(
                        "4.2s",
                        class_name="text-xs px-2 py-1 rounded-full bg-[#f1f3f4] dark:bg-gray-800 text-[#5f6368] dark:text-gray-400 ml-auto",
                    ),
                ),
                class_name="flex items-center justify-between mt-2",
            ),
            class_name="flex-1 min-w-0 flex flex-col",
        ),
        class_name=[
            "flex group max-w-4xl mx-auto w-full px-4 py-6 rounded-2xl hover:bg-[#f8f9fa] dark:hover:bg-white/5 transition-colors",
            rx.color_mode_cond("text-[#202124]", "text-gray-100"),
        ],
    )


# ============================================================================
# CHAT INPUT COMPONENTS
# ============================================================================


def model_selector() -> rx.Component:
    """AI model selection dropdown."""
    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.icon("sparkles", size=16, class_name="text-blue-500"),
                rx.text(ChatState.model_display_name),
                rx.icon("chevron-down", size=14, class_name="text-gray-400"),
                variant="ghost",
                class_name="flex items-center gap-2 text-gray-600 font-medium hover:text-gray-900 cursor-pointer",
            ),
        ),
        rx.popover.content(
            rx.box(
                rx.text(
                    "Select Model",
                    class_name="text-sm font-semibold text-gray-700 mb-2",
                ),
                # Anthropic models
                rx.box(
                    rx.text(
                        "Anthropic",
                        class_name="text-xs font-semibold text-gray-500 mb-1",
                    ),
                    rx.button(
                        "Claude Sonnet 4.5",
                        on_click=lambda: ChatState.set_selected_model(
                            "claude-sonnet-4-5"
                        ),
                        class_name=[
                            "w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm",
                            rx.cond(
                                ChatState.selected_model == "claude-sonnet-4-5",
                                "bg-blue-50 text-blue-700 font-medium",
                                "text-gray-700",
                            ),
                        ],
                    ),
                    rx.button(
                        "Claude Sonnet 4",
                        on_click=lambda: ChatState.set_selected_model(
                            "claude-sonnet-4"
                        ),
                        class_name=[
                            "w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm",
                            rx.cond(
                                ChatState.selected_model == "claude-sonnet-4",
                                "bg-blue-50 text-blue-700 font-medium",
                                "text-gray-700",
                            ),
                        ],
                    ),
                    rx.button(
                        "Claude Opus 4",
                        on_click=lambda: ChatState.set_selected_model("claude-opus-4"),
                        class_name=[
                            "w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm",
                            rx.cond(
                                ChatState.selected_model == "claude-opus-4",
                                "bg-blue-50 text-blue-700 font-medium",
                                "text-gray-700",
                            ),
                        ],
                    ),
                    class_name="mb-3",
                ),
                # OpenAI models
                rx.box(
                    rx.text(
                        "OpenAI",
                        class_name="text-xs font-semibold text-gray-500 mb-1",
                    ),
                    rx.button(
                        "GPT-4o",
                        on_click=lambda: ChatState.set_selected_model("gpt-4o"),
                        class_name=[
                            "w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm",
                            rx.cond(
                                ChatState.selected_model == "gpt-4o",
                                "bg-blue-50 text-blue-700 font-medium",
                                "text-gray-700",
                            ),
                        ],
                    ),
                    rx.button(
                        "GPT-4o Mini",
                        on_click=lambda: ChatState.set_selected_model("gpt-4o-mini"),
                        class_name=[
                            "w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm",
                            rx.cond(
                                ChatState.selected_model == "gpt-4o-mini",
                                "bg-blue-50 text-blue-700 font-medium",
                                "text-gray-700",
                            ),
                        ],
                    ),
                    rx.button(
                        "o1",
                        on_click=lambda: ChatState.set_selected_model("o1"),
                        class_name=[
                            "w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm",
                            rx.cond(
                                ChatState.selected_model == "o1",
                                "bg-blue-50 text-blue-700 font-medium",
                                "text-gray-700",
                            ),
                        ],
                    ),
                    rx.button(
                        "o1 Mini",
                        on_click=lambda: ChatState.set_selected_model("o1-mini"),
                        class_name=[
                            "w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm",
                            rx.cond(
                                ChatState.selected_model == "o1-mini",
                                "bg-blue-50 text-blue-700 font-medium",
                                "text-gray-700",
                            ),
                        ],
                    ),
                ),
                class_name="p-2",
            ),
            class_name="bg-white rounded-lg shadow-lg border border-gray-200 min-w-[200px]",
        ),
    )


def thinking_selector() -> rx.Component:
    """Thinking/reasoning level selector."""
    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.icon(
                    "brain",
                    size=16,
                    class_name=rx.cond(
                        ChatState.enable_reasoning_bool,
                        "text-orange-500",
                        "text-gray-400",
                    ),
                ),
                rx.text(
                    "Think",
                    class_name=rx.cond(
                        ChatState.enable_reasoning_bool,
                        "text-orange-600 font-medium",
                        "text-gray-500",
                    ),
                ),
                rx.text(
                    rx.cond(
                        ChatState.enable_reasoning_bool,
                        rx.cond(
                            ChatState.reasoning_budget_int >= 16000,
                            "High",
                            rx.cond(
                                ChatState.reasoning_budget_int >= 2000, "Medium", "Low"
                            ),
                        ),
                        "Off",
                    ),
                    class_name="text-xs text-gray-400",
                ),
                rx.icon("chevron-down", size=14, class_name="text-gray-400"),
                variant="ghost",
                class_name="flex items-center gap-2 hover:text-orange-700 cursor-pointer",
            ),
        ),
        rx.popover.content(
            rx.box(
                rx.text(
                    "Reasoning Mode",
                    class_name="text-sm font-semibold text-gray-700 mb-3",
                ),
                # Toggle reasoning
                rx.box(
                    rx.switch(
                        checked=ChatState.enable_reasoning_bool,
                        on_change=ChatState.set_enable_reasoning,
                    ),
                    rx.text(
                        "Enable Extended Thinking",
                        class_name="text-sm text-gray-700",
                    ),
                    class_name="flex items-center gap-3 mb-3 pb-3 border-b border-gray-200",
                ),
                # Reasoning budget slider (only visible when enabled)
                rx.cond(
                    ChatState.enable_reasoning_bool,
                    rx.box(
                        rx.text(
                            "Thinking Budget",
                            class_name="text-xs font-semibold text-gray-500 mb-2",
                        ),
                        rx.button(
                            "Low (2k tokens)",
                            on_click=lambda: ChatState.set_reasoning_budget(2000),
                            class_name=[
                                "w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm",
                                rx.cond(
                                    ChatState.reasoning_budget_int < 2000,
                                    "bg-orange-50 text-orange-700 font-medium",
                                    "text-gray-700",
                                ),
                            ],
                        ),
                        rx.button(
                            "Medium (8k tokens)",
                            on_click=lambda: ChatState.set_reasoning_budget(8000),
                            class_name=[
                                "w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm",
                                rx.cond(
                                    (ChatState.reasoning_budget_int >= 2000)
                                    & (ChatState.reasoning_budget_int < 16000),
                                    "bg-orange-50 text-orange-700 font-medium",
                                    "text-gray-700",
                                ),
                            ],
                        ),
                        rx.button(
                            "High (16k+ tokens)",
                            on_click=lambda: ChatState.set_reasoning_budget(16000),
                            class_name=[
                                "w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm",
                                rx.cond(
                                    ChatState.reasoning_budget_int >= 16000,
                                    "bg-orange-50 text-orange-700 font-medium",
                                    "text-gray-700",
                                ),
                            ],
                        ),
                        rx.text(
                            "Higher budgets allow deeper reasoning but cost more tokens.",
                            class_name="text-xs text-gray-400 mt-2",
                        ),
                    ),
                    rx.box(),  # Empty box when reasoning is disabled
                ),
                class_name="p-2",
            ),
            class_name="bg-white rounded-lg shadow-lg border border-gray-200 min-w-[250px]",
        ),
    )


def temperature_selector() -> rx.Component:
    """Temperature control slider."""
    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.icon("thermometer", size=16, class_name="text-blue-500"),
                rx.text(
                    "Temp",
                    class_name="text-blue-600 font-medium",
                ),
                rx.text(
                    f"{ChatState.temperature:.1f}",
                    class_name="text-xs text-gray-400",
                ),
                rx.icon("chevron-down", size=14, class_name="text-gray-400"),
                variant="ghost",
                class_name="flex items-center gap-2 hover:text-blue-700 cursor-pointer",
            ),
        ),
        rx.popover.content(
            rx.box(
                rx.text(
                    "Temperature",
                    class_name="text-sm font-semibold text-gray-700 mb-2",
                ),
                rx.text(
                    f"Current: {ChatState.temperature:.1f}",
                    class_name="text-xs text-gray-500 mb-3",
                ),
                rx.slider(
                    value=[ChatState.temperature],
                    on_value_commit=lambda value: ChatState.set_temperature(value[0]),
                    min=0.0,
                    max=2.0,
                    step=0.1,
                    class_name="mb-3",
                ),
                rx.box(
                    rx.button(
                        "Precise (0.3)",
                        on_click=lambda: ChatState.set_temperature(0.3),
                        class_name="text-xs px-2 py-1 rounded hover:bg-gray-100",
                    ),
                    rx.button(
                        "Balanced (0.7)",
                        on_click=lambda: ChatState.set_temperature(0.7),
                        class_name="text-xs px-2 py-1 rounded hover:bg-gray-100",
                    ),
                    rx.button(
                        "Creative (1.2)",
                        on_click=lambda: ChatState.set_temperature(1.2),
                        class_name="text-xs px-2 py-1 rounded hover:bg-gray-100",
                    ),
                    class_name="flex gap-2",
                ),
                rx.text(
                    "Lower = more focused, Higher = more creative",
                    class_name="text-xs text-gray-400 mt-2",
                ),
                class_name="p-2",
            ),
            class_name="bg-white rounded-lg shadow-lg border border-gray-200 min-w-[250px]",
        ),
    )


def input_tools_left() -> rx.Component:
    """Left side tools: model selector, think, temp."""
    return rx.box(
        model_selector(),
        thinking_selector(),
        temperature_selector(),
        class_name="flex items-center gap-4",
    )


def input_tools_right() -> rx.Component:
    """Right side tools: grid, add, run."""
    return rx.box(
        rx.button(
            rx.icon("layout-grid", size=16),
            variant="ghost",
            class_name="w-8 h-8 rounded-full bg-transparent text-[#5f6368] dark:text-gray-400 hover:bg-[#e8eaed] dark:hover:bg-gray-700 flex items-center justify-center cursor-pointer transition",
        ),
        rx.button(
            rx.icon("plus", size=16),
            variant="outline",
            class_name="w-8 h-8 rounded-full border border-[#dadce0] dark:border-gray-600 bg-white dark:bg-transparent text-[#5f6368] dark:text-gray-400 hover:bg-[#f1f3f4] dark:hover:bg-gray-700 flex items-center justify-center cursor-pointer transition",
        ),
        rx.button(
            rx.icon("send", size=16),
            on_click=ChatState.handle_send_message,
            class_name="w-10 h-10 rounded-full bg-[#1967d2] text-white hover:bg-[#1557b0] flex items-center justify-center cursor-pointer shadow-md transition-transform active:scale-95 border-none",
        ),
        class_name="flex items-center gap-2",
    )


def chat_input() -> rx.Component:
    """Complete chat input area with textarea and tools."""
    return rx.box(
        rx.box(
            # Textarea
            rx.text_area(
                placeholder="Start typing a prompt, use option + enter to append",
                value=ChatState.input_text,
                on_change=ChatState.set_input_text,
                rows="1",
                auto_height=True,
                class_name=[
                    "w-full resize-none outline-none bg-transparent border-0 focus:ring-0 px-3 py-3 text-[15px]",
                    rx.color_mode_cond(
                        "text-[#202124] placeholder-[#5f6368]",
                        "text-gray-200 placeholder-gray-400",
                    ),
                ],
            ),
            # Toolbar
            rx.box(
                input_tools_left(),
                input_tools_right(),
                class_name="flex justify-between items-center pt-1 pb-1 px-2",
            ),
            class_name=[
                # rounded-xl = 12px, matching Google AI Studio card shape
                # google-shadow = custom multi-layer shadow defined in styles.css
                "max-w-3xl mx-auto rounded-xl px-3 pt-2 pb-1 transition-all"
                " border focus-within:border-[#aecbfa] dark:border-transparent dark:focus-within:border-[#4a90d9]"
                " google-shadow",
                rx.color_mode_cond(
                    "bg-[#f8f9fa] border-[#e0e0e0]",
                    "bg-[#1e1f20] border-gray-700",
                ),
            ],
        ),
        class_name=[
            "px-6 pb-6 pt-4",
            rx.color_mode_cond("bg-white", "bg-[#111827]"),
        ],
    )


# ============================================================================
# MAIN CHAT AREA COMPONENTS
# ============================================================================


def global_search() -> rx.Component:
    """Top global search bar."""
    return rx.box(
        rx.box(
            rx.icon(
                "search",
                size=16,
                class_name="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#5f6368] dark:text-gray-400",
            ),
            rx.input(
                placeholder="Search",
                value=ChatState.sidebar_search,
                on_change=ChatState.set_sidebar_search,
                class_name=[
                    "w-full rounded-full py-2 pl-10 pr-4 border focus:outline-none focus:border-[#1967d2]",
                    rx.color_mode_cond(
                        "border-[#dadce0] bg-white text-[#202124] placeholder-[#5f6368]",
                        "border-gray-600 bg-gray-800 text-gray-100 placeholder-gray-500",
                    ),
                ],
            ),
            class_name="relative w-full max-w-2xl",
        ),
        class_name=[
            "p-4 border-b flex justify-center",
            rx.color_mode_cond("border-[#dadce0]", "border-gray-700"),
        ],
    )


def chat_header() -> rx.Component:
    """Chat header matching AI Studio toolbar."""
    return rx.box(
        # Left side: Menu toggle, title, token count
        rx.box(
            rx.icon(
                "menu",
                size=20,
                class_name="text-[#5f6368] dark:text-gray-400 mr-4 cursor-pointer hidden md:block",
            ),
            rx.heading(
                "Playground",
                class_name=[
                    "text-[22px] font-normal",
                    rx.color_mode_cond("text-[#202124]", "text-gray-200"),
                ],
            ),
            rx.box(
                rx.text("159 tokens", class_name="text-xs font-medium"),
                class_name=[
                    "ml-4 px-3 py-1 rounded-full border cursor-help",
                    rx.color_mode_cond(
                        "bg-[#f1f3f4] border-[#dadce0] text-[#5f6368]",
                        "bg-gray-800 border-gray-700 text-gray-300",
                    ),
                ],
            ),
            class_name="flex items-center",
        ),
        # Right side: Theme picker + standard actions
        rx.box(
            rx.color_mode_cond(
                rx.select(
                    list(LIGHT_CODE_THEMES),
                    value=ChatState.light_code_theme,
                    on_change=ChatState.set_light_code_theme,
                    placeholder="Light theme",
                    size="1",
                    class_name="text-xs",
                ),
                rx.select(
                    list(DARK_CODE_THEMES),
                    value=ChatState.code_theme,
                    on_change=ChatState.set_code_theme,
                    placeholder="Dark theme",
                    size="1",
                    class_name="text-xs",
                ),
            ),
            rx.button(
                rx.icon("pen-tool", size=18),
                variant="ghost",
                class_name="text-[#5f6368] dark:text-gray-400 hover:bg-[#f1f3f4] dark:hover:bg-gray-800 rounded-full w-10 h-10 cursor-pointer",
            ),
            rx.button(
                rx.icon("plus", size=18),
                variant="ghost",
                class_name="text-[#5f6368] dark:text-gray-400 hover:bg-[#f1f3f4] dark:hover:bg-gray-800 rounded-full w-10 h-10 cursor-pointer",
            ),
            rx.button(
                rx.icon("more-vertical", size=18),
                variant="ghost",
                class_name="text-[#5f6368] dark:text-gray-400 hover:bg-[#f1f3f4] dark:hover:bg-gray-800 rounded-full w-10 h-10 cursor-pointer",
            ),
            rx.button(
                rx.icon("sliders-horizontal", size=18),
                variant="ghost",
                class_name=[
                    "rounded-full w-10 h-10 cursor-pointer",
                    rx.color_mode_cond(
                        "text-[#1967d2] bg-[#e8f0fe] hover:bg-[#d2e3fc]",
                        "text-blue-300 bg-blue-900/30 hover:bg-blue-900/50",
                    ),
                ],
            ),
            class_name="flex items-center gap-2",
        ),
        class_name=[
            "px-6 py-3 border-b flex justify-between items-center",
            rx.color_mode_cond(
                "border-[#dadce0] bg-white",
                "border-gray-800 bg-[#1e1f20]",
            ),
        ],
    )


def chat_history() -> rx.Component:
    """Scrollable chat message history."""
    return rx.box(
        rx.foreach(
            ChatState.messages,
            lambda message, index: message_bubble(message, index),
        ),
        class_name="flex-1 overflow-y-auto p-8 space-y-8",
    )


def chat_area() -> rx.Component:
    """Complete main chat area component."""
    return rx.el.main(
        global_search(),
        chat_header(),
        chat_history(),
        chat_input(),
        class_name=[
            "flex-1 flex flex-col h-full relative min-w-0",
            rx.color_mode_cond("bg-white", "bg-[#111827]"),
        ],
    )
