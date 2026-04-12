"""Main page layout combining all components."""

import reflex as rx

# ARCHITECT FIX: Importing from the new Vertical Slices!
from mychat_reflex.features.workspace.ui import sidebar
from mychat_reflex.features.chat.ui import chat_area


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
        class_name="bg-white text-gray-800 font-sans antialiased h-screen w-full overflow-hidden flex",
    )
