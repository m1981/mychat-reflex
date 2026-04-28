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
                rx.color_mode_cond("text-[#202124]", "text-gray-100"),
            ],
        ),
        class_name=[
            "p-5 border-b",
            rx.color_mode_cond("border-[#dadce0]", "border-gray-700"),
        ],
    )


def action_buttons() -> rx.Component:
    """New chat and New folder buttons."""
    return rx.box(
        rx.button(
            rx.icon("plus", size=16),
            rx.text("New chat"),
            on_click=ChatState.create_new_chat,
            variant="surface",
            class_name="flex-1 flex justify-center items-center gap-2 bg-[#e8f0fe] text-[#1967d2] hover:bg-[#d2e3fc] dark:bg-blue-900/30 dark:text-blue-200 dark:hover:bg-blue-900/50 py-2 px-4 rounded-full text-sm font-medium transition cursor-pointer shadow-none border-none",
        ),
        rx.button(
            rx.icon("folder-plus", size=16),
            on_click=ChatState.create_new_folder,
            variant="ghost",
            class_name="bg-white border border-[#dadce0] text-[#5f6368] hover:bg-[#f1f3f4] dark:bg-transparent dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800 p-2 rounded-full transition cursor-pointer shadow-sm",
        ),
        class_name="p-4 flex gap-2 items-center",
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
                    "w-full rounded-md py-1.5 px-3 text-sm border focus:outline-none focus:border-[#1967d2]",
                    rx.color_mode_cond(
                        "border-[#dadce0] bg-white text-[#202124] placeholder-[#5f6368]",
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
        rx.button(
            rx.icon(
                "message-square",
                size=14,
                class_name="mr-2 text-[#5f6368] dark:text-gray-400",
            ),
            chat_title,
            on_click=lambda: ChatState.select_chat(chat_id),
            variant="ghost",
            class_name="w-full justify-start text-left bg-transparent text-[#3c4043] hover:bg-[#e8eaed] hover:text-[#202124] dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white py-2 px-3 rounded-full text-sm font-medium transition-colors cursor-pointer",
        ),
        class_name="list-none",
    )


def folder_section(folder_name: str, chats: list[tuple[str, str]]) -> rx.Component:
    """A folder with its chat items."""
    return rx.box(
        rx.box(
            folder_name,
            class_name="text-xs font-semibold text-[#5f6368] dark:text-gray-500 uppercase tracking-wider px-3 mb-2 mt-4",
        ),
        rx.el.ul(
            *[chat_item(chat_id, chat_title) for chat_id, chat_title in chats],
            class_name="space-y-0.5",
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
            variant="ghost",
            class_name=[
                "flex items-center gap-3 font-medium w-full cursor-pointer",
                rx.color_mode_cond(
                    "text-[#3c4043] hover:text-[#202124] hover:bg-[#f1f3f4]",
                    "text-gray-300 hover:text-white",
                ),
            ],
        ),
        rx.button(
            rx.box(
                class_name=[
                    "w-6 h-6 rounded-full border flex items-center justify-center",
                    rx.color_mode_cond(
                        "border-[#dadce0] bg-[#e8eaed]", "border-gray-600 bg-gray-700"
                    ),
                ],
            ),
            rx.text("Michal"),
            variant="ghost",
            class_name=[
                "flex items-center gap-3 font-medium w-full cursor-pointer",
                rx.color_mode_cond(
                    "text-[#3c4043] hover:text-[#202124] hover:bg-[#f1f3f4]",
                    "text-gray-300 hover:text-white",
                ),
            ],
        ),
        class_name=[
            "p-4 border-t space-y-4",
            rx.color_mode_cond("border-[#dadce0]", "border-gray-700"),
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
            "w-[280px] flex-shrink-0 border-r flex flex-col h-full",
            rx.color_mode_cond(
                "border-[#dadce0] bg-[#f8f9fa]", "border-gray-700 bg-[#1e1f20]"
            ),
        ],
    )
