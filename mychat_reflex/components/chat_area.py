"""Main chat area component with header, messages, and input."""

import reflex as rx
from ..state.chat_state import ChatState
from .message import message_bubble
from .chat_input import chat_input


def global_search() -> rx.Component:
    """Top global search bar."""
    return rx.box(
        rx.box(
            rx.icon(
                "search",
                size=16,
                class_name="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400",
            ),
            rx.input(
                placeholder="Search",
                value=ChatState.global_search,
                on_change=ChatState.set_global_search,
                class_name="w-full border border-gray-400 rounded-full py-2 pl-10 pr-4 focus:outline-none focus:border-blue-500",
            ),
            class_name="relative w-full max-w-2xl",
        ),
        class_name="p-4 border-b border-gray-300 flex justify-center",
    )


def chat_header() -> rx.Component:
    """Chat header with title and action buttons."""
    return rx.box(
        # Left side: title and edit button
        rx.box(
            rx.heading(
                ChatState.current_chat_title,
                class_name="text-lg font-semibold text-gray-800",
            ),
            rx.button(
                rx.icon("pencil", size=14),
                class_name="text-gray-400 hover:text-gray-600 cursor-pointer",
            ),
            class_name="flex items-center gap-3",
        ),
        # Right side: action buttons
        rx.box(
            rx.button(
                rx.icon("boxes", size=16),
                class_name="hover:text-gray-800 cursor-pointer",
            ),
            rx.button(
                rx.icon("plus", size=16),
                class_name="hover:text-gray-800 cursor-pointer",
            ),
            rx.button(
                rx.icon("ellipsis-vertical", size=16),
                class_name="hover:text-gray-800 cursor-pointer",
            ),
            rx.button(
                rx.icon("sliders-horizontal", size=16),
                class_name="hover:text-gray-800 cursor-pointer",
            ),
            class_name="flex items-center gap-4 text-gray-500",
        ),
        class_name="px-8 py-4 border-b border-gray-300 flex justify-between items-center",
    )


def chat_history() -> rx.Component:
    """Scrollable chat message history."""
    return rx.box(
        rx.foreach(
            ChatState.messages,
            message_bubble,
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
        class_name="flex-1 flex flex-col h-full relative min-w-0 bg-white",
    )
