"""Chat message bubble component."""

from __future__ import annotations

import reflex as rx
from typing import Optional
from ..state.chat_state import ChatState, Message


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
                    message.timestamp,
                    class_name="text-xs text-gray-400 font-medium",
                ),
                message_actions(message.id),
                class_name="flex items-center justify-between mb-1",
            ),
            # Message content - split by newlines for multiple paragraphs
            rx.box(
                rx.foreach(
                    message.content.split("\n"),
                    lambda para: rx.cond(
                        para.strip() != "",
                        rx.text(
                            para,
                            class_name="text-gray-700 leading-relaxed mb-2",
                        ),
                        rx.box(),  # Empty box for blank lines
                    ),
                ),
            ),
            class_name="flex-1",
        ),
        class_name="flex gap-4 group max-w-4xl mx-auto w-full",
    )
