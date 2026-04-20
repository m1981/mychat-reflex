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


def sidebar_header() -> rx.Component:
    """App logo and title."""
    return rx.box(
        rx.heading(
            "Super Chat",
            class_name=[
                "text-2xl font-bold tracking-wide",
                rx.color_mode_cond("text-gray-800", "text-gray-100"),
            ],
        ),
        class_name=[
            "p-5 border-b",
            rx.color_mode_cond("border-gray-300", "border-gray-700"),
        ],
    )


def action_buttons() -> rx.Component:
    """New chat and New folder buttons."""
    return rx.box(
        rx.button(
            "New chat",
            on_click=ChatState.create_new_chat,
            class_name="flex-1 bg-green-200 border border-green-400 text-green-900 py-1.5 px-2 rounded-md text-sm font-medium hover:bg-green-300 transition cursor-pointer",
        ),
        rx.button(
            "New folder",
            on_click=ChatState.create_new_folder,
            class_name="flex-1 bg-green-200 border border-green-400 text-green-900 py-1.5 px-2 rounded-md text-sm font-medium hover:bg-green-300 transition cursor-pointer",
        ),
        class_name="p-4 flex gap-2",
    )


def sidebar_search() -> rx.Component:
    """Search input for filtering chats."""
    return rx.box(
        rx.box(
            rx.input(
                placeholder="Search",
                value=ChatState.sidebar_search,
                on_change=ChatState.set_sidebar_search,
                class_name=[
                    "w-full rounded-md py-1.5 px-3 text-sm border focus:outline-none focus:border-blue-500",
                    rx.color_mode_cond(
                        "border-gray-400 bg-white text-gray-800",
                        "border-gray-600 bg-gray-800 text-gray-100 placeholder-gray-500",
                    ),
                ],
            ),
            class_name="relative",
        ),
        class_name="px-4 mb-4",
    )


def chat_item(chat_id: str, chat_title: str) -> rx.Component:
    """Individual chat item in the navigation."""
    return rx.el.li(
        chat_title,
        on_click=lambda: ChatState.select_chat(chat_id),
        class_name="cursor-pointer hover:text-blue-600",
    )


def folder_section(folder_name: str, chats: list[tuple[str, str]]) -> rx.Component:
    """A folder with its chat items."""
    return rx.box(
        rx.box(
            folder_name,
            class_name="bg-blue-200 border border-blue-400 text-blue-900 px-3 py-1.5 rounded-md font-medium text-sm mb-2 cursor-pointer",
        ),
        rx.el.ul(
            *[chat_item(chat_id, chat_title) for chat_id, chat_title in chats],
            class_name=[
                "ml-4 space-y-2 text-sm font-medium",
                rx.color_mode_cond("text-gray-700", "text-gray-300"),
            ],
        ),
    )


def navigation_list() -> rx.Component:
    """Main navigation with folders and chats."""
    return rx.el.nav(
        # Job offers folder
        folder_section(
            "Job offers",
            [
                ("cv-update", "CV update"),
                ("email-prep", "Email preparation"),
            ],
        ),
        # ESP32 projects folder
        folder_section(
            "ESP32 projects",
            [
                ("esp32-overview", "ESP32 overview"),
                ("first-project", "First ESP project"),
            ],
        ),
        class_name="flex-1 overflow-y-auto px-4 space-y-4",
    )


def sidebar_footer() -> rx.Component:
    """Settings and profile section."""
    return rx.box(
        rx.color_mode.button(size="2", cursor="pointer"),
        rx.button(
            rx.icon("settings", class_name="text-lg"),
            rx.text("Settings"),
            class_name=[
                "flex items-center gap-3 font-medium w-full cursor-pointer",
                rx.color_mode_cond(
                    "text-gray-700 hover:text-black", "text-gray-300 hover:text-white"
                ),
            ],
        ),
        rx.button(
            rx.box(
                class_name=[
                    "w-6 h-6 rounded-full border flex items-center justify-center",
                    rx.color_mode_cond(
                        "border-gray-400 bg-gray-100", "border-gray-600 bg-gray-700"
                    ),
                ],
            ),
            rx.text("Michal"),
            class_name=[
                "flex items-center gap-3 font-medium w-full cursor-pointer",
                rx.color_mode_cond(
                    "text-gray-700 hover:text-black", "text-gray-300 hover:text-white"
                ),
            ],
        ),
        class_name=[
            "p-4 border-t space-y-4",
            rx.color_mode_cond("border-gray-300", "border-gray-700"),
        ],
    )


def sidebar() -> rx.Component:
    """Complete left sidebar component."""
    return rx.el.aside(
        sidebar_header(),
        action_buttons(),
        sidebar_search(),
        navigation_list(),
        sidebar_footer(),
        class_name=[
            "w-64 flex-shrink-0 border-r flex flex-col h-full",
            rx.color_mode_cond(
                "border-gray-300 bg-white", "border-gray-700 bg-gray-900"
            ),
        ],
    )
