"""
Knowledge Base Feature UI Components.

Contains the right sidebar notes panel.
"""

import reflex as rx

# FIXME (Architecture Debt):
# Rule #4 states we should not import state from other features.
# For MVP Phase 2, we are importing ChatState because all state is currently centralized there.
# In Phase 4, we must extract KnowledgeBaseState and update these bindings.
from mychat_reflex.features.chat.state import ChatState


def notes_header() -> rx.Component:
    """Notes panel header."""
    return rx.box(
        rx.heading(
            "Notes tab",
            class_name="text-xl font-semibold text-gray-800",
        ),
        class_name="p-4 border-b border-gray-200",
    )


def notes_content() -> rx.Component:
    """Notes content area."""
    return rx.box(
        rx.cond(
            ChatState.notes_content == "",
            rx.text(
                "Empty notes...",
                class_name="text-gray-400 text-sm italic",
            ),
            rx.el.textarea(
                value=ChatState.notes_content,
                # Note: on_change handler is missing in original code,
                # will need to be added to state later if notes are editable
                placeholder="Add your notes here...",
                class_name="w-full h-full resize-none outline-none text-gray-700 text-sm",
            ),
        ),
        class_name="flex-1 p-4 overflow-y-auto",
    )
