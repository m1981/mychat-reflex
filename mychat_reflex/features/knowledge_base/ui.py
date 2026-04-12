"""
Knowledge Base Feature UI Components.

Contains the right sidebar notes panel.
"""

import reflex as rx

from .state import KnowledgeBaseState


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
            KnowledgeBaseState.notes_content == "",
            rx.text(
                "Empty notes...",
                class_name="text-gray-400 text-sm italic",
            ),
            rx.el.textarea(
                value=KnowledgeBaseState.notes_content,
                on_change=KnowledgeBaseState.set_notes_content,
                placeholder="Add your notes here...",
                class_name="w-full h-full resize-none outline-none text-gray-700 text-sm",
            ),
        ),
        class_name="flex-1 p-4 overflow-y-auto",
    )


# ✅ CRITICAL FIX: This function was missing!
def notes_panel() -> rx.Component:
    """Complete right sidebar notes panel."""
    return rx.el.aside(
        rx.box(
            notes_header(),
            notes_content(),
            class_name="border border-gray-300 rounded-2xl h-full bg-white flex flex-col overflow-hidden shadow-sm",
        ),
        class_name="w-80 flex-shrink-0 border-l border-gray-300 hidden lg:flex flex-col p-4 bg-gray-50/50",
    )
