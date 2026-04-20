"""
Chat Feature UI Components.

Contains all UI elements for the chat bounded context:
- Message bubbles
- Chat input area
- Chat history and layout
"""

import reflex as rx
from typing import Optional

from .state import ChatState
from .models import Message


# ============================================================================
# HELPERS
# ============================================================================


def _code_block(text, **props):
    """Render a code block with the current theme. Used in rx.markdown component_map.
    Language is omitted when unknown — rx.code_block language prop is a strict Literal type."""
    lang = props.get("className", "").replace("language-", "")
    extra = {"language": lang} if lang else {}
    return rx.code_block(
        text,
        **extra,
        theme=ChatState.code_theme,
        show_line_numbers=False,
        wrap_long_lines=True,
        width="100%",
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
            class_name="hover:text-gray-700 cursor-pointer",
        ),
        rx.button(
            rx.icon("pencil", size=14),
            class_name="hover:text-gray-700 cursor-pointer",
        ),
        rx.button(
            rx.icon("trash-2", size=14),
            on_click=lambda: ChatState.delete_message(message_id),
            class_name="hover:text-gray-700 cursor-pointer",
        ),
        rx.button(
            rx.icon("rotate-cw", size=14),
            on_click=lambda: ChatState.regenerate_message(message_id),
            class_name="hover:text-gray-700 cursor-pointer",
        ),
        class_name="flex gap-3 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity",
    )


def user_avatar(avatar_url: Optional[str]) -> rx.Component:
    """User avatar image."""
    return rx.cond(
        avatar_url,
        rx.image(
            src=avatar_url,
            alt="User",
            class_name="w-8 h-8 rounded-full border border-gray-300",
        ),
        rx.box(
            rx.icon("user", size=16),
            class_name="w-8 h-8 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center border border-gray-300",
        ),
    )


def ai_avatar() -> rx.Component:
    """AI assistant avatar."""
    return rx.box(
        rx.icon("sparkles", size=16),
        class_name="w-8 h-8 rounded-full bg-blue-100 text-blue-500 flex items-center justify-center border border-blue-200",
    )


def message_bubble(message: Message) -> rx.Component:
    """A single message bubble (user or AI)."""
    return rx.box(
        # Avatar
        rx.cond(
            message.is_user,
            user_avatar(message.avatar_url),
            ai_avatar(),
        ),
        # Content
        rx.box(
            # Header with timestamp and actions
            rx.box(
                rx.text(
                    message.timestamp_formatted,  # ARCHITECT FIX: Updated to match new rx.Model
                    class_name="text-xs text-gray-400 font-medium",
                ),
                message_actions(message.id),
                class_name="flex items-center justify-between mb-1",
            ),
            # Message content rendered as Markdown with syntax highlighting
            rx.box(
                rx.markdown(
                    message.content,
                    class_name="prose max-w-none text-gray-700 leading-relaxed",
                    component_map={"code": _code_block},
                ),
            ),
            class_name="flex-1",
        ),
        class_name="flex gap-4 group max-w-4xl mx-auto w-full",
    )


# ============================================================================
# CHAT INPUT COMPONENTS
# ============================================================================


def model_selector() -> rx.Component:
    """AI model selection dropdown."""
    return rx.button(
        rx.icon("sparkles", size=16, class_name="text-blue-500"),
        rx.text(ChatState.selected_model),
        class_name="flex items-center gap-2 text-gray-600 font-medium hover:text-gray-900 cursor-pointer",
    )


def input_tools_left() -> rx.Component:
    """Left side tools: model selector, think, temp."""
    return rx.box(
        model_selector(),
        rx.button(
            "Think",
            class_name="text-orange-500 font-medium hover:text-orange-600 cursor-pointer",
        ),
        rx.button(
            "Temp",
            class_name="text-blue-500 font-medium hover:text-blue-600 cursor-pointer",
        ),
        class_name="flex items-center gap-4",
    )


def input_tools_right() -> rx.Component:
    """Right side tools: grid, add, run."""
    return rx.box(
        rx.button(
            rx.icon("layout-grid", size=16),
            class_name="w-8 h-8 rounded bg-gray-100 text-gray-500 hover:bg-gray-200 flex items-center justify-center cursor-pointer",
        ),
        rx.button(
            rx.icon("plus", size=16),
            class_name="w-8 h-8 rounded-full border border-gray-300 text-gray-500 hover:bg-gray-50 flex items-center justify-center cursor-pointer",
        ),
        rx.button(
            rx.text("Run"),
            rx.icon("corner-down-left", size=12, class_name="text-gray-400"),
            on_click=ChatState.handle_send_message,  # ARCHITECT FIX: Updated to new method name
            class_name="border border-gray-300 rounded-lg px-4 py-1.5 text-gray-700 font-medium hover:bg-gray-50 flex items-center gap-2 cursor-pointer",
        ),
        class_name="flex items-center gap-3",
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
                rows="2",
                class_name="w-full resize-none outline-none text-gray-700 placeholder-gray-400 bg-transparent border-0",
            ),
            # Toolbar
            rx.box(
                input_tools_left(),
                input_tools_right(),
                class_name="flex justify-between items-center mt-3 pt-2 border-t border-gray-100",
            ),
            class_name="max-w-4xl mx-auto border border-gray-300 rounded-2xl p-4 shadow-sm focus-within:border-blue-400 focus-within:ring-1 focus-within:ring-blue-400 transition-all",
        ),
        class_name="p-6 bg-white",
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
                class_name="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400",
            ),
            rx.input(
                placeholder="Search",
                value=ChatState.sidebar_search,
                on_change=ChatState.set_sidebar_search,
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
        # Right side: action buttons + theme picker
        rx.box(
            rx.select(
                [
                    "one-dark",
                    "atom-dark",
                    "dracula",
                    "nord",
                    "night-owl",
                    "vs-dark",
                    "solarized-dark",
                    "material-oceanic",
                ],
                value=ChatState.code_theme,
                on_change=ChatState.set_code_theme,
                placeholder="Code theme",
                size="1",
                class_name="text-xs",
            ),
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
