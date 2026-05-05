import reflex as rx
from reflex.components.datadisplay.shiki_code_block import ShikiHighLevelCodeBlock

from .state import ChatState
from .models import Message
from ...ui.primitives import T, pill_btn, icon_btn, icon_btn_square, popover

# ============================================================================
# CODE / MARKDOWN
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
    return ShikiHighLevelCodeBlock.create(
        text,
        language=props.get("language"),
        theme="nord",
        themes=DYNAMIC_CODE_THEME_CONFIG,
        show_line_numbers=False,
        wrap_long_lines=True,
        width="100%",
    )


def _fast_code_block(text, **props):
    return rx.el.pre(
        rx.el.code(text),
        class_name=(
            f"my-4 p-4 rounded-lg overflow-x-auto text-sm font-mono {T['code_block']}"
        ),
    )


def _message_markdown(content: str, is_streaming: bool) -> rx.Component:
    classes = f"prose max-w-none leading-relaxed text-[15px] {T['prose_body']}"
    return rx.cond(
        is_streaming,
        rx.markdown(
            content, class_name=classes, component_map={"pre": _fast_code_block}
        ),
        rx.markdown(
            content, class_name=classes, component_map={"pre": _shiki_code_block}
        ),
    )


def message_actions(message: Message) -> rx.Component:
    """Action buttons for a message."""
    btn_cls = (
        f"h-7 w-7 rounded-md flex items-center justify-center cursor-pointer "
        f"transition-colors {T['btn_action']}"
    )

    def _btn(icon, on_click=None):
        return rx.el.button(
            rx.icon(icon, size=14), on_click=on_click, class_name=btn_cls
        )

    return rx.el.div(
        _btn("copy", ChatState.copy_message(message.id)),
        # Edit button (Only for User messages)
        rx.cond(
            message.role == "user",
            _btn("pencil", lambda: ChatState.start_edit(message.id, message.content)),
            rx.fragment(),
        ),
        _btn("trash-2", ChatState.delete_message(message.id)),
        # Regenerate button (Uses the new request_regenerate flow with the warning modal)
        _btn("rotate-cw", lambda: ChatState.request_regenerate(message.id)),
        class_name="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity",
    )


def message_bubble(message: Message, index: int) -> rx.Component:
    """A single message bubble (user or AI) with inline editing."""
    is_last = index == (ChatState.messages.length() - 1)
    is_streaming = is_last & ChatState.is_generating
    is_editing = ChatState.editing_message_id == message.id

    # The standard markdown view
    standard_view = rx.el.div(
        _message_markdown(message.content, is_streaming),
        rx.el.div(
            message_actions(message),  # Pass the whole message object now
            rx.cond(
                message.role != "user",
                rx.el.span(
                    "4.2s",
                    class_name=f"ml-auto text-xs px-2 py-0.5 rounded-full {T['badge_muted']}",
                ),
            ),
            class_name="flex items-center mt-3",
        ),
    )

    # The edit mode view
    edit_view = rx.el.div(
        rx.text_area(
            value=ChatState.edit_content,
            on_change=ChatState.set_edit_content,
            class_name=f"w-full p-3 rounded-lg border {T['border_divider']} {T['surface_app']} focus:ring-2 outline-none text-sm mb-3",
            rows="4",
        ),
        rx.el.div(
            rx.button(
                "Cancel",
                on_click=ChatState.cancel_edit,
                variant="soft",
                color_scheme="gray",
                size="2",
            ),
            rx.button("Save & Submit", on_click=ChatState.save_edit, size="2"),
            class_name="flex justify-end gap-2",
        ),
    )

    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.cond(message.role == "user", "User", "Model"),
                    class_name=f"text-sm font-semibold {T['text_primary']}",
                ),
                rx.moment(
                    message.created_at,
                    format="LT",
                    class_name=f"text-xs {T['text_muted']}",
                ),
                class_name="flex items-baseline gap-2 mb-1.5",
            ),
            # Toggle between standard view and edit view
            rx.cond(is_editing, edit_view, standard_view),
            class_name="flex-1 min-w-0",
        ),
        class_name=(
            f"group max-w-4xl mx-auto w-full px-5 py-5 rounded-2xl "
            f"transition-colors {T['text_primary']} {T['surface_hover_soft']}"
        ),
    )


# ============================================================================
# TOOLBAR SELECTORS (Radix popovers, rx.el.button triggers)
# ============================================================================


def _popover_item(label: str, value: str, active_cond, on_click) -> rx.Component:
    return rx.el.button(
        label,
        on_click=on_click,
        class_name=rx.cond(
            active_cond,
            f"{T['popover_item']} {T['item_active_blue']}",
            f"{T['popover_item']} {T['item_inactive']}",
        ),
    )


def model_selector() -> rx.Component:
    trigger = pill_btn(
        rx.icon("sparkles", size=15, class_name="text-indigo-500 flex-shrink-0"),
        rx.el.span(ChatState.model_display_name, class_name="text-sm font-medium"),
        rx.icon("chevron-down", size=13, class_name=T["text_faint"]),
    )

    content = rx.el.div(
        rx.el.p("Select model", class_name=T["popover_title"]),
        rx.el.div(
            rx.el.p("Anthropic", class_name=T["popover_label"]),
            _popover_item(
                "Claude Sonnet 4.5",
                "claude-sonnet-4-5",
                ChatState.selected_model == "claude-sonnet-4-5",
                lambda: ChatState.set_selected_model("claude-sonnet-4-5"),
            ),
            _popover_item(
                "Claude Sonnet 4",
                "claude-sonnet-4",
                ChatState.selected_model == "claude-sonnet-4",
                lambda: ChatState.set_selected_model("claude-sonnet-4"),
            ),
            _popover_item(
                "Claude Opus 4",
                "claude-opus-4",
                ChatState.selected_model == "claude-opus-4",
                lambda: ChatState.set_selected_model("claude-opus-4"),
            ),
            class_name="mb-2",
        ),
        rx.el.div(
            rx.el.p("OpenAI", class_name=T["popover_label"]),
            _popover_item(
                "GPT-4o",
                "gpt-4o",
                ChatState.selected_model == "gpt-4o",
                lambda: ChatState.set_selected_model("gpt-4o"),
            ),
            _popover_item(
                "GPT-4o Mini",
                "gpt-4o-mini",
                ChatState.selected_model == "gpt-4o-mini",
                lambda: ChatState.set_selected_model("gpt-4o-mini"),
            ),
            _popover_item(
                "o1",
                "o1",
                ChatState.selected_model == "o1",
                lambda: ChatState.set_selected_model("o1"),
            ),
        ),
    )

    return popover(trigger, content, min_width="220px")


def _budget_item(label: str, value: int, active_cond) -> rx.Component:
    return rx.el.button(
        label,
        on_click=lambda: ChatState.set_reasoning_budget(value),
        class_name=rx.cond(
            active_cond,
            f"{T['popover_item']} {T['item_active_amber']}",
            f"{T['popover_item']} {T['item_inactive']}",
        ),
    )


def thinking_selector() -> rx.Component:
    enabled = ChatState.enable_reasoning_bool
    budget = ChatState.reasoning_budget_int

    trigger = pill_btn(
        rx.icon(
            "brain",
            size=15,
            class_name=rx.cond(enabled, "text-amber-500", T["text_faint"]),
        ),
        rx.el.span(
            "Think",
            class_name=rx.cond(
                enabled,
                f"text-sm font-medium {T['text_amber']}",
                "text-sm font-medium",
            ),
        ),
        rx.el.span(
            rx.cond(
                enabled,
                rx.cond(
                    budget >= 16000, "High", rx.cond(budget >= 2000, "Medium", "Low")
                ),
                "Off",
            ),
            class_name=f"text-xs {T['text_faint']}",
        ),
        rx.icon("chevron-down", size=13, class_name=T["text_faint"]),
    )

    content = rx.el.div(
        rx.el.p("Reasoning mode", class_name=T["popover_title"]),
        rx.el.div(
            rx.switch(checked=enabled, on_change=ChatState.set_enable_reasoning),
            rx.el.span(
                "Enable extended thinking",
                class_name=f"text-sm {T['text_secondary']}",
            ),
            class_name=(
                f"flex items-center gap-3 px-1 mb-3 pb-3 border-b {T['border_divider']}"
            ),
        ),
        rx.cond(
            enabled,
            rx.el.div(
                rx.el.p("Thinking budget", class_name=T["popover_label"]),
                _budget_item("Low (2k tokens)", 2000, budget < 2000),
                _budget_item(
                    "Medium (8k tokens)", 8000, (budget >= 2000) & (budget < 16000)
                ),
                _budget_item("High (16k+ tokens)", 16000, budget >= 16000),
                rx.el.p(
                    "Higher budgets allow deeper reasoning but cost more tokens.",
                    class_name=T["popover_hint"],
                ),
            ),
            rx.el.div(),
        ),
    )

    return popover(trigger, content, min_width="260px")


def temperature_selector() -> rx.Component:
    preset_cls = (
        f"text-xs px-2 py-1 rounded-md transition-colors {T['surface_hover']} "
        f"{T['text_secondary']} cursor-pointer"
    )

    trigger = pill_btn(
        rx.icon("thermometer", size=15, class_name="text-indigo-500 flex-shrink-0"),
        rx.el.span("Temp", class_name=f"text-sm font-medium {T['accent_text']}"),
        rx.el.span(
            ChatState.temperature,
            class_name=f"text-xs {T['text_faint']}",
        ),
        rx.icon("chevron-down", size=13, class_name=T["text_faint"]),
    )

    content = rx.el.div(
        rx.el.p("Temperature", class_name=T["popover_title"]),
        rx.el.p(
            "Current: " + ChatState.temperature,
            class_name=f"text-xs mb-3 px-1 {T['text_muted']}",
        ),
        rx.slider(
            value=[ChatState.temperature_float],
            on_value_commit=lambda v: ChatState.set_temperature(v[0]),
            min=0.0,
            max=2.0,
            step=0.1,
            class_name="mb-3 px-1",
        ),
        rx.el.div(
            rx.el.button(
                "Precise (0.3)",
                on_click=lambda: ChatState.set_temperature(0.3),
                class_name=preset_cls,
            ),
            rx.el.button(
                "Balanced (0.7)",
                on_click=lambda: ChatState.set_temperature(0.7),
                class_name=preset_cls,
            ),
            rx.el.button(
                "Creative (1.2)",
                on_click=lambda: ChatState.set_temperature(1.2),
                class_name=preset_cls,
            ),
            class_name="flex gap-1",
        ),
        rx.el.p(
            "Lower = more focused · Higher = more creative",
            class_name=T["popover_hint"],
        ),
    )

    return popover(trigger, content, min_width="260px")


# ... (Keep temperature_selector as is) ...


def _input_left() -> rx.Component:
    return rx.el.div(
        icon_btn_square(
            "key",
            extra=T["btn_blue_tint"],
        ),
        model_selector(),
        thinking_selector(),
        temperature_selector(),
        pill_btn(
            rx.icon("layout-grid", size=14, class_name="flex-shrink-0"),
            rx.el.span("Tools", class_name="text-sm font-medium leading-none"),
        ),
        class_name="flex items-center gap-2 flex-shrink-0 flex-wrap",
    )


def _input_right() -> rx.Component:
    return rx.el.div(
        icon_btn("mic"),
        icon_btn("plus"),
        pill_btn(
            rx.el.span("Run", class_name="text-sm font-medium leading-none"),
            rx.el.span("⌘ ↵", class_name=f"text-xs leading-none {T['text_faint']}"),
            on_click=ChatState.handle_send_message,
            extra="gap-2 px-3.5",
        ),
        class_name="flex items-center gap-2 flex-shrink-0",
    )


def chat_input() -> rx.Component:
    return rx.el.footer(
        rx.el.div(
            rx.text_area(
                placeholder="Start typing a prompt to see what our models can do",
                value=ChatState.input_text,
                on_change=ChatState.set_input_text,
                rows="2",
                auto_height=True,
                class_name=(
                    f"w-full resize-none outline-none bg-transparent border-0 "
                    f"focus:ring-0 px-4 py-3.5 text-[15px] leading-relaxed "
                    f"{T['text_primary']} {T['placeholder']}"
                ),
            ),
            rx.el.div(
                _input_left(),
                _input_right(),
                class_name=(
                    f"flex justify-between items-center gap-4 "
                    f"px-2 py-1.5 border-t {T['border_divider']}"
                ),
            ),
            class_name=(
                f"max-w-4xl mx-auto w-full rounded-xl border overflow-hidden "
                f"transition-all shadow-sm focus-within:ring-1 {T['input_wrapper']}"
            ),
        ),
        class_name=f"px-6 pb-6 pt-2 w-full {T['surface_app']}",
    )


def chat_header() -> rx.Component:
    icon_cls = (
        f"h-9 w-9 rounded-full flex items-center justify-center "
        f"cursor-pointer transition-colors "
        f"{T['text_secondary']} {T['surface_hover']}"
    )

    return rx.el.header(
        rx.el.div(
            rx.icon(
                "menu",
                size=18,
                class_name=f"mr-3 cursor-pointer hidden md:block {T['text_secondary']}",
            ),
            rx.el.h1(
                "Playground", class_name=f"text-xl font-medium {T['text_primary']}"
            ),
            rx.el.div(
                rx.el.span("159 tokens", class_name="text-xs font-medium"),
                class_name=(
                    f"ml-3 px-2.5 py-0.5 rounded-full border cursor-help {T['badge_outline']}"
                ),
            ),
            class_name="flex items-center",
        ),
        rx.el.div(
            # 1. LIGHT THEME SELECTOR (Hidden in dark mode)
            rx.el.div(
                rx.select(
                    list(LIGHT_CODE_THEMES),
                    value=ChatState.light_code_theme,
                    on_change=ChatState.set_light_code_theme,
                    placeholder="Light theme",
                    size="1",
                ),
                class_name="block dark:hidden",
            ),
            # 2. DARK THEME SELECTOR (Hidden in light mode)
            rx.el.div(
                rx.select(
                    list(DARK_CODE_THEMES),
                    value=ChatState.code_theme,
                    on_change=ChatState.set_code_theme,
                    placeholder="Dark theme",
                    size="1",
                ),
                class_name="hidden dark:block",
            ),
            rx.el.button(rx.icon("pen-tool", size=17), class_name=icon_cls),
            rx.el.button(rx.icon("plus", size=17), class_name=icon_cls),
            rx.el.button(rx.icon("more-vertical", size=17), class_name=icon_cls),
            rx.el.button(
                rx.icon("sliders-horizontal", size=17),
                class_name=f"h-9 w-9 rounded-full flex items-center justify-center cursor-pointer transition-colors {T['accent_pill']}",
            ),
            class_name="flex items-center gap-1",
        ),
        class_name=(
            f"px-6 py-2.5 border-b flex justify-between items-center "
            f"{T['border_divider']} {T['surface_app']}"
        ),
    )


# ============================================================================
# HISTORY + LAYOUT
# ============================================================================


def global_search() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "search",
                size=15,
                class_name=f"absolute left-3.5 top-1/2 -translate-y-1/2 {T['text_faint']}",
            ),
            rx.el.input(
                placeholder="Search",
                value=ChatState.sidebar_search,
                on_change=ChatState.set_sidebar_search,
                class_name=(
                    f"w-full rounded-full py-1.5 pl-9 pr-4 text-sm border outline-none "
                    f"transition focus:ring-2 {T['input_search']}"
                ),
            ),
            class_name="relative w-full max-w-2xl",
        ),
        class_name=(
            f"px-4 py-3 border-b flex justify-center "
            f"{T['border_divider']} {T['surface_app']}"
        ),
    )


def chat_history() -> rx.Component:
    return rx.el.div(
        rx.foreach(
            ChatState.messages,
            lambda message, index: message_bubble(message, index),
        ),
        class_name="flex-1 overflow-y-auto px-6 py-6 space-y-2",
    )


def chat_area() -> rx.Component:
    return rx.el.main(
        global_search(),
        chat_header(),
        chat_history(),
        chat_input(),
        class_name=f"flex-1 flex flex-col h-full relative min-w-0 {T['surface_app']}",
    )
