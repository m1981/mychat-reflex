"""
Workspace Feature UI Components.

Contains the left sidebar, folder navigation, and chat selection.
"""

import reflex as rx

# FIXME (Architecture Debt):
# Rule #4 states we should not import state from other features.
# For MVP Phase 2, we are importing ChatState because all state is currently centralized there.
# In Phase 4, we must extract WorkspaceState and update these bindings.
from mychat_reflex.features.chat.state import ChatState


# ============================================================================
# THEME HELPERS
# ============================================================================
# We use `rx.color_mode_cond` for ALL theme-aware classes so the in-app
# Reflex color-mode toggle works correctly. (Tailwind v4's default `dark:`
# variant follows the OS preference, not Reflex's toggle.)


def cm(light: str, dark: str):
    """Pick a class string based on Reflex's current color mode."""
    return rx.color_mode_cond(light, dark)


def cls(*parts):
    """Compose base class strings with conditional theme parts."""
    return list(parts)


# Shared theme tokens (kept aligned with chat/ui.py)
SURFACE_SIDEBAR = cm("bg-zinc-50", "bg-zinc-950")
SURFACE_HOVER_NAV = cm("hover:bg-zinc-200/60", "hover:bg-zinc-800")
BORDER_DIVIDER = cm("border-zinc-200", "border-zinc-800")
TEXT_PRIMARY = cm("text-zinc-900", "text-zinc-100")
TEXT_SECONDARY = cm("text-zinc-700", "text-zinc-300")
TEXT_HOVER = cm("hover:text-zinc-900", "hover:text-white")
TEXT_LABEL = cm("text-zinc-500", "text-zinc-500")
TEXT_ICON = cm("text-zinc-400", "text-zinc-500")

NAV_ITEM_BASE = (
    "w-full justify-start text-left bg-transparent rounded-lg "
    "text-sm font-normal py-1.5 px-3 transition-colors cursor-pointer"
)

FOOTER_BTN_BASE = (
    "flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium "
    "cursor-pointer transition-colors"
)


# ============================================================================
# COMPONENTS
# ============================================================================


def sidebar_header() -> rx.Component:
    """App logo and title."""
    return rx.box(
        rx.heading(
            "Super Chat",
            class_name=cls(
                "text-lg font-semibold tracking-tight",
                TEXT_PRIMARY,
            ),
        ),
        class_name=cls("px-5 py-4 border-b", BORDER_DIVIDER),
    )


def action_buttons() -> rx.Component:
    """New chat and New folder buttons."""
    return rx.box(
        rx.button(
            rx.icon("plus", size=15),
            rx.text("New chat"),
            on_click=ChatState.create_new_chat,
            variant="surface",
            class_name=cls(
                "flex-1 flex justify-center items-center gap-2 "
                "py-2 px-4 rounded-full text-sm font-medium border-none shadow-none "
                "text-white transition-colors cursor-pointer",
                cm(
                    "bg-indigo-600 hover:bg-indigo-700",
                    "bg-indigo-500 hover:bg-indigo-400",
                ),
            ),
        ),
        rx.button(
            rx.icon("folder-plus", size=15),
            on_click=ChatState.create_new_folder,
            variant="ghost",
            class_name=cls(
                "p-2 rounded-full border transition-colors cursor-pointer",
                cm(
                    "bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-100",
                    "bg-transparent border-zinc-700 text-zinc-400 hover:bg-zinc-800",
                ),
            ),
        ),
        class_name="px-4 py-3 flex gap-2 items-center",
    )


def sidebar_search() -> rx.Component:
    """Search input for filtering chats."""
    return rx.box(
        rx.input(
            placeholder="Search",
            value=ChatState.sidebar_search,
            on_change=ChatState.set_sidebar_search,
            class_name=cls(
                "w-full rounded-lg py-1.5 px-3 text-sm border outline-none transition focus:ring-2",
                cm(
                    "bg-white border-zinc-200 text-zinc-900 placeholder-zinc-400 "
                    "focus:border-indigo-400 focus:ring-indigo-100",
                    "bg-zinc-900 border-zinc-800 text-zinc-100 placeholder-zinc-500 "
                    "focus:border-indigo-500 focus:ring-indigo-500/10",
                ),
            ),
        ),
        class_name="px-4 mb-3",
    )


def chat_item(chat_id: str, chat_title: str) -> rx.Component:
    """Individual chat item in the navigation."""
    return rx.el.li(
        rx.button(
            rx.icon("message-square", size=14, class_name=cls("mr-2", TEXT_ICON)),
            chat_title,
            on_click=lambda: ChatState.select_chat(chat_id),
            variant="ghost",
            class_name=cls(
                NAV_ITEM_BASE,
                TEXT_SECONDARY,
                SURFACE_HOVER_NAV,
                TEXT_HOVER,
            ),
        ),
        class_name="list-none",
    )


def folder_section(folder_name: str, chats: list[tuple[str, str]]) -> rx.Component:
    """A folder with its chat items."""
    return rx.box(
        rx.box(
            folder_name,
            class_name=cls(
                "text-[11px] font-semibold uppercase tracking-wider px-3 mb-1.5 mt-3",
                TEXT_LABEL,
            ),
        ),
        rx.el.ul(
            *[chat_item(chat_id, chat_title) for chat_id, chat_title in chats],
            class_name="space-y-0.5",
        ),
    )


def navigation_list() -> rx.Component:
    """Main navigation with folders and chats."""
    return rx.el.nav(
        folder_section(
            "Job offers",
            [
                ("cv-update", "CV update"),
                ("email-prep", "Email preparation"),
            ],
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


def sidebar_footer() -> rx.Component:
    """Settings and profile section."""
    footer_btn_cls = cls(
        FOOTER_BTN_BASE,
        TEXT_SECONDARY,
        SURFACE_HOVER_NAV,
        TEXT_HOVER,
    )

    return rx.box(
        rx.color_mode.button(size="2", cursor="pointer"),
        rx.button(
            rx.icon("settings", size=16),
            rx.text("Settings"),
            variant="ghost",
            class_name=footer_btn_cls,
        ),
        rx.button(
            rx.box(
                class_name=cls(
                    "w-6 h-6 rounded-full border flex items-center justify-center",
                    cm(
                        "border-zinc-200 bg-zinc-100",
                        "border-zinc-700 bg-zinc-800",
                    ),
                ),
            ),
            rx.text("Michal"),
            variant="ghost",
            class_name=footer_btn_cls,
        ),
        class_name=cls("px-3 py-3 border-t space-y-1", BORDER_DIVIDER),
    )


def sidebar() -> rx.Component:
    """Complete left sidebar component."""
    return rx.el.aside(
        sidebar_header(),
        action_buttons(),
        sidebar_search(),
        navigation_list(),
        sidebar_footer(),
        class_name=cls(
            "w-[260px] flex-shrink-0 flex flex-col h-full border-r",
            SURFACE_SIDEBAR,
            cm("border-zinc-200", "border-zinc-800"),
        ),
    )
