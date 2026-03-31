"""Main page layout combining all components."""

import reflex as rx
from ..components.sidebar import sidebar
from ..components.chat_area import chat_area
from ..components.notes_panel import notes_panel


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
        class_name="bg-white text-gray-800 font-sans antialiased h-screen w-full overflow-hidden flex",
    )
