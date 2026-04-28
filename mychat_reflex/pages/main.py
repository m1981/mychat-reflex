"""Main page layout combining all components."""

import reflex as rx

# ARCHITECT FIX: Importing from the new Vertical Slices!
from mychat_reflex.features.workspace.ui import sidebar
from mychat_reflex.features.chat.ui import chat_area
from mychat_reflex.features.knowledge_base.ui import notes_panel


def main_page() -> rx.Component:
    """
    Main application page with three-column layout:
    - Left sidebar: navigation, folders, settings
    - Center: chat area with messages and input
    - Right sidebar: notes panel
    """
    return rx.box(
        sidebar(),
        chat_area(),
        notes_panel(),
        class_name=[
            "font-sans h-screen w-full overflow-hidden flex",
            rx.color_mode_cond("bg-white text-[#202124]", "bg-[#111827] text-gray-100"),
        ],
    )
