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
# THEME HELPER
# ============================================================================
# Reflex's `rx.color_mode` toggle adds/removes the `.dark` class on <html>,
# but Tailwind v4 by default makes `dark:` variants react to the OS
# `prefers-color-scheme` media query — NOT to that class. To respect the
# in-app toggle without touching the css file, we route every theme-aware
# class through `rx.color_mode_cond(light, dark)`.
#
# `cm(light, dark)` is a tiny wrapper that returns the conditional, and
# `cls(*parts)` joins a base class string with one or more `cm(...)` parts.


def cm(light: str, dark: str):
    """Pick a class string based on Reflex's current color mode."""
    return rx.color_mode_cond(light, dark)


def cls(*parts):
    """Compose a base class string with conditional theme parts.

    Usage:
        class_name=cls("rounded-lg px-3", cm("bg-white", "bg-zinc-900"))
    """
    return list(parts)


# ============================================================================
# DESIGN TOKENS — semantic theme pairs
# ============================================================================
# Light: zinc neutrals on white. Dark: zinc on near-black. Accent: indigo.

# Surfaces
SURFACE_APP = cm("bg-white", "bg-zinc-950")
SURFACE_RAISED = cm("bg-zinc-50", "bg-zinc-900")
SURFACE_HOVER = cm("hover:bg-zinc-100", "hover:bg-zinc-800")
SURFACE_HOVER_SOFT = cm("hover:bg-zinc-50", "hover:bg-zinc-900/50")

# Borders
BORDER = cm("border-zinc-200", "border-zinc-800")
BORDER_DIVIDER = cm("border-zinc-200", "border-zinc-800")

# Text
TEXT_PRIMARY = cm("text-zinc-900", "text-zinc-100")
TEXT_SECONDARY = cm("text-zinc-600", "text-zinc-400")
TEXT_MUTED = cm("text-zinc-500", "text-zinc-500")
TEXT_FAINT = cm("text-zinc-400", "text-zinc-500")
PLACEHOLDER = cm("placeholder-zinc-400", "placeholder-zinc-500")

# Accent (indigo) and warning (amber, for "thinking")
ACCENT_TEXT = cm("text-indigo-600", "text-indigo-400")
ACCENT_PILL = cm(
    "text-indigo-600 bg-indigo-50 hover:bg-indigo-100",
    "text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20",
)
ITEM_ACTIVE_BLUE = cm(
    "bg-indigo-50 text-indigo-700 font-medium",
    "bg-indigo-500/10 text-indigo-300 font-medium",
)
ITEM_ACTIVE_AMBER = cm(
    "bg-amber-50 text-amber-700 font-medium",
    "bg-amber-500/10 text-amber-300 font-medium",
)
ITEM_INACTIVE = cm("text-zinc-700", "text-zinc-300")

# Inputs
INPUT_BASE = (
    "w-full rounded-lg py-1.5 px-3 text-sm border outline-none transition focus:ring-2"
)
INPUT_THEME = cm(
    "bg-white border-zinc-200 text-zinc-900 placeholder-zinc-400 "
    "focus:border-indigo-400 focus:ring-indigo-100",
    "bg-zinc-900 border-zinc-800 text-zinc-100 placeholder-zinc-500 "
    "focus:border-indigo-500 focus:ring-indigo-500/10",
)

# Reusable component class fragments (theme-independent base + theme part)
ICON_BTN_BASE = (
    "h-9 w-9 rounded-full flex items-center justify-center cursor-pointer "
    "transition-colors"
)
ICON_BTN_THEME = cm(
    "text-zinc-500 hover:bg-zinc-100",
    "text-zinc-400 hover:bg-zinc-800",
)

POPOVER_PANEL_BASE = "p-2 rounded-xl border shadow-lg"
POPOVER_PANEL_THEME = cm(
    "bg-white border-zinc-200",
    "bg-zinc-900 border-zinc-800",
)

POPOVER_ITEM_BASE = "w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors"
POPOVER_ITEM_HOVER = cm("hover:bg-zinc-100", "hover:bg-zinc-800")

POPOVER_LABEL = "text-xs font-semibold uppercase tracking-wide mb-1.5 px-1"
POPOVER_LABEL_THEME = cm("text-zinc-500", "text-zinc-400")
POPOVER_TITLE = "text-sm font-semibold mb-2 px-1"
POPOVER_TITLE_THEME = cm("text-zinc-800", "text-zinc-200")
POPOVER_HINT = "text-xs mt-2 px-1"
POPOVER_HINT_THEME = cm("text-zinc-500", "text-zinc-500")

TOOLBAR_TRIGGER_BASE = (
    "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium "
    "transition-colors cursor-pointer"
)
TOOLBAR_TRIGGER_THEME = cm(
    "text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100",
    "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800",
)


# ============================================================================
# CODE / MARKDOWN HELPERS
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
    return rx.el.pre(
        rx.el.code(text),
        class_name=cls(
            "my-4 p-4 rounded-lg overflow-x-auto text-sm font-mono",
            cm("bg-zinc-100 text-zinc-800", "bg-zinc-900 text-zinc-200"),
        ),
    )


STATIC_MARKDOWN_MAP = {"pre": _shiki_code_block}
STREAMING_MARKDOWN_MAP = {"pre": _fast_code_block}


def _message_markdown(content: str, is_streaming: bool) -> rx.Component:
    """Render markdown, choosing the safe renderer if currently streaming."""
    classes = cls(
        "prose max-w-none leading-relaxed text-[15px]",
        cm("prose-zinc", "prose-invert"),
    )
    return rx.cond(
        is_streaming,
        rx.markdown(content, class_name=classes, component_map=STREAMING_MARKDOWN_MAP),
        rx.markdown(content, class_name=classes, component_map=STATIC_MARKDOWN_MAP),
    )


# ============================================================================
# MESSAGE BUBBLE COMPONENTS
# ============================================================================


def message_actions(message_id: str) -> rx.Component:
    """Action buttons for a message (copy, edit, delete, regenerate)."""
    btn_base = (
        "h-7 w-7 rounded-md flex items-center justify-center cursor-pointer "
        "transition-colors"
    )
    btn_theme = cm(
        "text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100",
        "text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800",
    )

    def _btn(icon, on_click=None):
        kw = {"on_click": on_click} if on_click else {}
        return rx.button(
            rx.icon(icon, size=14),
            variant="ghost",
            class_name=cls(btn_base, btn_theme),
            **kw,
        )

    return rx.box(
        _btn("copy", lambda: ChatState.copy_message(message_id)),
        _btn("pencil"),
        _btn("trash-2", lambda: ChatState.delete_message(message_id)),
        _btn("rotate-cw", lambda: ChatState.regenerate_message(message_id)),
        class_name="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity",
    )


def message_bubble(message: Message, index: int) -> rx.Component:
    """A single message bubble (user or AI)."""
    is_last_message = index == (ChatState.messages.length() - 1)
    is_currently_streaming = is_last_message & ChatState.is_generating

    return rx.box(
        rx.box(
            # Header: author + timestamp
            rx.box(
                rx.text(
                    rx.cond(message.is_user, "User", "Model"),
                    class_name=cls("text-sm font-semibold", TEXT_PRIMARY),
                ),
                rx.text(
                    message.timestamp_formatted,
                    class_name=cls("text-xs", TEXT_MUTED),
                ),
                class_name="flex items-baseline gap-2 mb-1.5",
            ),
            # Content
            _message_markdown(message.content, is_currently_streaming),
            # Footer: actions + runtime
            rx.box(
                message_actions(message.id),
                rx.cond(
                    ~message.is_user,
                    rx.text(
                        "4.2s",
                        class_name=cls(
                            "ml-auto text-xs px-2 py-0.5 rounded-full",
                            cm(
                                "bg-zinc-100 text-zinc-500",
                                "bg-zinc-800 text-zinc-400",
                            ),
                        ),
                    ),
                ),
                class_name="flex items-center mt-3",
            ),
            class_name="flex-1 min-w-0",
        ),
        class_name=cls(
            "group max-w-4xl mx-auto w-full px-5 py-5 rounded-2xl transition-colors",
            TEXT_PRIMARY,
            SURFACE_HOVER_SOFT,
        ),
    )


# ============================================================================
# CHAT INPUT — TOOLBAR SELECTORS
# ============================================================================


def _model_item(label: str, value: str) -> rx.Component:
    return rx.button(
        label,
        on_click=lambda: ChatState.set_selected_model(value),
        class_name=cls(
            POPOVER_ITEM_BASE,
            POPOVER_ITEM_HOVER,
            rx.cond(
                ChatState.selected_model == value,
                ITEM_ACTIVE_BLUE,
                ITEM_INACTIVE,
            ),
        ),
    )


def model_selector() -> rx.Component:
    """AI model selection dropdown."""
    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.icon("sparkles", size=15, class_name="text-indigo-500"),
                rx.text(ChatState.model_display_name),
                rx.icon("chevron-down", size=13, class_name="text-zinc-400"),
                variant="ghost",
                class_name=cls(TOOLBAR_TRIGGER_BASE, TOOLBAR_TRIGGER_THEME),
            ),
        ),
        rx.popover.content(
            rx.box(
                rx.text(
                    "Select Model", class_name=cls(POPOVER_TITLE, POPOVER_TITLE_THEME)
                ),
                rx.box(
                    rx.text(
                        "Anthropic", class_name=cls(POPOVER_LABEL, POPOVER_LABEL_THEME)
                    ),
                    _model_item("Claude Sonnet 4.5", "claude-sonnet-4-5"),
                    _model_item("Claude Sonnet 4", "claude-sonnet-4"),
                    _model_item("Claude Opus 4", "claude-opus-4"),
                    class_name="mb-2",
                ),
                rx.box(
                    rx.text(
                        "OpenAI", class_name=cls(POPOVER_LABEL, POPOVER_LABEL_THEME)
                    ),
                    _model_item("GPT-4o", "gpt-4o"),
                    _model_item("GPT-4o Mini", "gpt-4o-mini"),
                    _model_item("o1", "o1"),
                    _model_item("o1 Mini", "o1-mini"),
                ),
            ),
            class_name=cls(POPOVER_PANEL_BASE, POPOVER_PANEL_THEME, "min-w-[220px]"),
        ),
    )


def _budget_item(label: str, value: int, is_active) -> rx.Component:
    return rx.button(
        label,
        on_click=lambda: ChatState.set_reasoning_budget(value),
        class_name=cls(
            POPOVER_ITEM_BASE,
            POPOVER_ITEM_HOVER,
            rx.cond(is_active, ITEM_ACTIVE_AMBER, ITEM_INACTIVE),
        ),
    )


def thinking_selector() -> rx.Component:
    """Thinking/reasoning level selector."""
    enabled = ChatState.enable_reasoning_bool
    budget = ChatState.reasoning_budget_int

    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.icon(
                    "brain",
                    size=15,
                    class_name=rx.cond(enabled, "text-amber-500", "text-zinc-400"),
                ),
                rx.text(
                    "Think",
                    class_name=rx.cond(
                        enabled,
                        cm("text-amber-600 font-medium", "text-amber-400 font-medium"),
                        "",
                    ),
                ),
                rx.text(
                    rx.cond(
                        enabled,
                        rx.cond(
                            budget >= 16000,
                            "High",
                            rx.cond(budget >= 2000, "Medium", "Low"),
                        ),
                        "Off",
                    ),
                    class_name=cls("text-xs", TEXT_FAINT),
                ),
                rx.icon("chevron-down", size=13, class_name="text-zinc-400"),
                variant="ghost",
                class_name=cls(TOOLBAR_TRIGGER_BASE, TOOLBAR_TRIGGER_THEME),
            ),
        ),
        rx.popover.content(
            rx.box(
                rx.text(
                    "Reasoning Mode", class_name=cls(POPOVER_TITLE, POPOVER_TITLE_THEME)
                ),
                rx.box(
                    rx.switch(
                        checked=enabled,
                        on_change=ChatState.set_enable_reasoning,
                    ),
                    rx.text(
                        "Enable Extended Thinking",
                        class_name=cls("text-sm", TEXT_SECONDARY),
                    ),
                    class_name=cls(
                        "flex items-center gap-3 px-1 mb-3 pb-3 border-b",
                        BORDER_DIVIDER,
                    ),
                ),
                rx.cond(
                    enabled,
                    rx.box(
                        rx.text(
                            "Thinking Budget",
                            class_name=cls(POPOVER_LABEL, POPOVER_LABEL_THEME),
                        ),
                        _budget_item("Low (2k tokens)", 2000, budget < 2000),
                        _budget_item(
                            "Medium (8k tokens)",
                            8000,
                            (budget >= 2000) & (budget < 16000),
                        ),
                        _budget_item("High (16k+ tokens)", 16000, budget >= 16000),
                        rx.text(
                            "Higher budgets allow deeper reasoning but cost more tokens.",
                            class_name=cls(POPOVER_HINT, POPOVER_HINT_THEME),
                        ),
                    ),
                    rx.box(),
                ),
            ),
            class_name=cls(POPOVER_PANEL_BASE, POPOVER_PANEL_THEME, "min-w-[260px]"),
        ),
    )


def temperature_selector() -> rx.Component:
    """Temperature control slider."""
    preset_btn_cls = cls(
        "text-xs px-2 py-1 rounded-md transition-colors",
        cm(
            "text-zinc-600 hover:bg-zinc-100",
            "text-zinc-400 hover:bg-zinc-800",
        ),
    )

    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.icon("thermometer", size=15, class_name="text-indigo-500"),
                rx.text(
                    "Temp",
                    class_name=cls("font-medium", ACCENT_TEXT),
                ),
                rx.text(
                    f"{ChatState.temperature:.1f}",
                    class_name=cls("text-xs", TEXT_FAINT),
                ),
                rx.icon("chevron-down", size=13, class_name="text-zinc-400"),
                variant="ghost",
                class_name=cls(TOOLBAR_TRIGGER_BASE, TOOLBAR_TRIGGER_THEME),
            ),
        ),
        rx.popover.content(
            rx.box(
                rx.text(
                    "Temperature", class_name=cls(POPOVER_TITLE, POPOVER_TITLE_THEME)
                ),
                rx.text(
                    f"Current: {ChatState.temperature:.1f}",
                    class_name=cls("text-xs mb-3 px-1", TEXT_MUTED),
                ),
                rx.slider(
                    value=[ChatState.temperature],
                    on_value_commit=lambda value: ChatState.set_temperature(value[0]),
                    min=0.0,
                    max=2.0,
                    step=0.1,
                    class_name="mb-3 px-1",
                ),
                rx.box(
                    rx.button(
                        "Precise (0.3)",
                        on_click=lambda: ChatState.set_temperature(0.3),
                        class_name=preset_btn_cls,
                    ),
                    rx.button(
                        "Balanced (0.7)",
                        on_click=lambda: ChatState.set_temperature(0.7),
                        class_name=preset_btn_cls,
                    ),
                    rx.button(
                        "Creative (1.2)",
                        on_click=lambda: ChatState.set_temperature(1.2),
                        class_name=preset_btn_cls,
                    ),
                    class_name="flex gap-1",
                ),
                rx.text(
                    "Lower = more focused, Higher = more creative",
                    class_name=cls(POPOVER_HINT, POPOVER_HINT_THEME),
                ),
            ),
            class_name=cls(POPOVER_PANEL_BASE, POPOVER_PANEL_THEME, "min-w-[260px]"),
        ),
    )


# ============================================================================
# CHAT INPUT
# ============================================================================


def input_tools_left() -> rx.Component:
    return rx.box(
        model_selector(),
        thinking_selector(),
        temperature_selector(),
        class_name="flex items-center gap-1",
    )


def input_tools_right() -> rx.Component:
    return rx.box(
        rx.button(
            rx.icon("layout-grid", size=16),
            variant="ghost",
            class_name=cls(ICON_BTN_BASE, ICON_BTN_THEME),
        ),
        rx.button(
            rx.icon("plus", size=16),
            variant="outline",
            class_name=cls(ICON_BTN_BASE, ICON_BTN_THEME, "border", BORDER),
        ),
        rx.button(
            rx.icon("send", size=16),
            on_click=ChatState.handle_send_message,
            class_name=(
                "h-10 w-10 rounded-full flex items-center justify-center "
                "bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm "
                "active:scale-95 transition cursor-pointer"
            ),
        ),
        class_name="flex items-center gap-1",
    )


def chat_input() -> rx.Component:
    """Complete chat input area with textarea and tools."""
    return rx.box(
        rx.box(
            rx.text_area(
                placeholder="Start typing a prompt, use option + enter to append",
                value=ChatState.input_text,
                on_change=ChatState.set_input_text,
                rows="1",
                auto_height=True,
                class_name=cls(
                    "w-full resize-none outline-none bg-transparent border-0 "
                    "focus:ring-0 px-3 py-3 text-[15px]",
                    TEXT_PRIMARY,
                    PLACEHOLDER,
                ),
            ),
            rx.box(
                input_tools_left(),
                input_tools_right(),
                class_name="flex justify-between items-center px-2 pb-1",
            ),
            class_name=cls(
                "max-w-3xl mx-auto rounded-2xl px-3 pt-2 pb-1 transition-all border",
                cm(
                    "bg-zinc-50 border-zinc-200 "
                    "focus-within:border-indigo-400 focus-within:ring-2 "
                    "focus-within:ring-indigo-100",
                    "bg-zinc-900 border-zinc-800 "
                    "focus-within:border-indigo-500 focus-within:ring-2 "
                    "focus-within:ring-indigo-500/10",
                ),
            ),
        ),
        class_name=cls("px-6 pb-6 pt-3", SURFACE_APP),
    )


# ============================================================================
# CHAT HEADER & SEARCH
# ============================================================================


def global_search() -> rx.Component:
    """Top global search bar."""
    return rx.box(
        rx.box(
            rx.icon(
                "search",
                size=15,
                class_name="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-400",
            ),
            rx.input(
                placeholder="Search",
                value=ChatState.sidebar_search,
                on_change=ChatState.set_sidebar_search,
                class_name=cls(
                    "w-full rounded-full py-1.5 pl-9 pr-4 text-sm border outline-none transition focus:ring-2",
                    INPUT_THEME,
                ),
            ),
            class_name="relative w-full max-w-2xl",
        ),
        class_name=cls(
            "px-4 py-3 border-b flex justify-center",
            BORDER_DIVIDER,
            SURFACE_APP,
        ),
    )


def chat_header() -> rx.Component:
    """Chat header matching AI Studio toolbar."""
    return rx.box(
        # Left: menu, title, token count
        rx.box(
            rx.icon(
                "menu",
                size=18,
                class_name=cls(
                    "mr-3 cursor-pointer hidden md:block",
                    TEXT_SECONDARY,
                ),
            ),
            rx.heading(
                "Playground",
                class_name=cls("text-xl font-medium", TEXT_PRIMARY),
            ),
            rx.box(
                rx.text("159 tokens", class_name="text-xs font-medium"),
                class_name=cls(
                    "ml-3 px-2.5 py-0.5 rounded-full border cursor-help",
                    cm(
                        "bg-zinc-100 border-zinc-200 text-zinc-600",
                        "bg-zinc-900 border-zinc-800 text-zinc-400",
                    ),
                ),
            ),
            class_name="flex items-center",
        ),
        # Right: theme picker + actions
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
                rx.icon("pen-tool", size=17),
                variant="ghost",
                class_name=cls(ICON_BTN_BASE, ICON_BTN_THEME),
            ),
            rx.button(
                rx.icon("plus", size=17),
                variant="ghost",
                class_name=cls(ICON_BTN_BASE, ICON_BTN_THEME),
            ),
            rx.button(
                rx.icon("more-vertical", size=17),
                variant="ghost",
                class_name=cls(ICON_BTN_BASE, ICON_BTN_THEME),
            ),
            rx.button(
                rx.icon("sliders-horizontal", size=17),
                variant="ghost",
                class_name=cls(
                    "h-9 w-9 rounded-full flex items-center justify-center "
                    "cursor-pointer transition-colors",
                    ACCENT_PILL,
                ),
            ),
            class_name="flex items-center gap-1",
        ),
        class_name=cls(
            "px-6 py-2.5 border-b flex justify-between items-center",
            BORDER_DIVIDER,
            SURFACE_APP,
        ),
    )


def chat_history() -> rx.Component:
    """Scrollable chat message history."""
    return rx.box(
        rx.foreach(
            ChatState.messages,
            lambda message, index: message_bubble(message, index),
        ),
        class_name="flex-1 overflow-y-auto px-6 py-6 space-y-2",
    )


def chat_area() -> rx.Component:
    """Complete main chat area component."""
    return rx.el.main(
        global_search(),
        chat_header(),
        chat_history(),
        chat_input(),
        class_name=cls(
            "flex-1 flex flex-col h-full relative min-w-0",
            SURFACE_APP,
        ),
    )
