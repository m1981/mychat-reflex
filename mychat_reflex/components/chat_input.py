"""Chat input area component with tools and model selector."""

import reflex as rx
from ..state.chat_state import ChatState


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
            on_click=ChatState.send_message,
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
