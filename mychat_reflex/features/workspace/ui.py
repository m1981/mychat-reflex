"""
features/workspace/ui.py

Left sidebar — folder navigation, chat list, footer actions.

Style rules:
- Import T and primitives from ui.primitives only
- rx.el.* everywhere, zero rx.button / rx.box
- WorkspaceState owns sidebar_search and folder state (Phase 4 target)
  For now ChatState is used under the FIXME note below
"""

import reflex as rx

# FIXME (Phase 4): extract WorkspaceState, remove this import
from mychat_reflex.features.chat.state import ChatState
from ...ui.primitives import T, nav_item, footer_btn


# ============================================================================
# SIDEBAR HEADER
# ============================================================================


def sidebar_header() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Super Chat",
            class_name=f"text-lg font-semibold tracking-tight {T['text_primary']}",
        ),
        class_name=f"px-5 py-4 border-b {T['border_divider']}",
    )


# ============================================================================
# ACTION BUTTONS
# ============================================================================


def action_buttons() -> rx.Component:
    return rx.el.div(
        # New chat — filled indigo pill
        rx.el.button(
            rx.icon("plus", size=15),
            rx.el.span("New chat"),
            on_click=ChatState.create_new_chat,
            class_name=(
                "flex-1 flex justify-center items-center gap-2 "
                "py-2 px-4 rounded-full text-sm font-medium "
                "text-white cursor-pointer transition-colors "
                "bg-indigo-600 hover:bg-indigo-700 "
                "dark:bg-indigo-500 dark:hover:bg-indigo-400"
            ),
        ),
        # New folder — ghost square
        rx.el.button(
            rx.icon("folder-plus", size=15),
            on_click=ChatState.create_new_folder,
            class_name=(
                "p-2 rounded-full border cursor-pointer transition-colors "
                "bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-100 "
                "dark:bg-transparent dark:border-zinc-700 "
                "dark:text-zinc-400 dark:hover:bg-zinc-800"
            ),
        ),
        class_name="px-4 py-3 flex gap-2 items-center",
    )


# ============================================================================
# SEARCH
# ============================================================================


def sidebar_search() -> rx.Component:
    return rx.el.div(
        rx.el.input(
            placeholder="Search",
            value=ChatState.sidebar_search,
            on_change=ChatState.set_sidebar_search,
            class_name=(
                "w-full rounded-lg py-1.5 px-3 text-sm border outline-none "
                "transition focus:ring-2 "
                "bg-white border-zinc-200 text-zinc-900 placeholder-zinc-400 "
                "focus:border-indigo-400 focus:ring-indigo-100 "
                "dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-100 "
                "dark:placeholder-zinc-500 dark:focus:border-indigo-500 "
                "dark:focus:ring-indigo-500/10"
            ),
        ),
        class_name="px-4 mb-3",
    )


# ============================================================================
# NAVIGATION
# ============================================================================


def chat_item(chat_id: str, chat_title: str) -> rx.Component:
    return rx.el.li(
        nav_item(
            rx.icon(
                "message-square",
                size=14,
                class_name=f"mr-2 flex-shrink-0 {T['text_faint']}",
            ),
            rx.el.span(chat_title),
            on_click=lambda: ChatState.select_chat(chat_id),
        ),
        class_name="list-none",
    )


def folder_section(
    folder_name: str,
    chats: list[tuple[str, str]],
) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            folder_name,
            class_name=(
                f"text-[11px] font-semibold uppercase tracking-wider "
                f"px-3 mb-1.5 mt-3 {T['text_muted']}"
            ),
        ),
        rx.el.ul(
            *[chat_item(cid, title) for cid, title in chats],
            class_name="space-y-0.5",
        ),
    )


def navigation_list() -> rx.Component:
    return rx.el.nav(
        folder_section(
            "Job offers",
            [("cv-update", "CV update"), ("email-prep", "Email preparation")],
        ),
        folder_section(
            "ESP32 projects",
            [
                ("esp32-overview", "ESP32 overview"),
                ("first-project", "First ESP project"),
            ],
        ),
        class_name="flex-1 overflow-y-auto px-2 pb-4",
    )


# ============================================================================
# FOOTER
# ============================================================================


def sidebar_footer() -> rx.Component:
    return rx.el.div(
        # Dark mode toggle (Radix built-in, no styling needed)
        rx.color_mode.button(size="2", cursor="pointer"),
        footer_btn(
            rx.icon("settings", size=16),
            rx.el.span("Settings"),
        ),
        footer_btn(
            # Avatar circle
            rx.el.div(
                class_name=(
                    "w-6 h-6 rounded-full border flex items-center justify-center "
                    "border-zinc-200 bg-zinc-100 "
                    "dark:border-zinc-700 dark:bg-zinc-800"
                ),
            ),
            rx.el.span("Michal"),
        ),
        class_name=f"px-3 py-3 border-t space-y-1 {T['border_divider']}",
    )


# ============================================================================
# SIDEBAR ROOT
# ============================================================================


def sidebar() -> rx.Component:
    return rx.el.aside(
        sidebar_header(),
        action_buttons(),
        sidebar_search(),
        navigation_list(),
        sidebar_footer(),
        class_name=(
            "w-[260px] flex-shrink-0 flex flex-col h-full border-r "
            "bg-zinc-50 dark:bg-zinc-950 "
            "border-zinc-200 dark:border-zinc-800"
        ),
    )
