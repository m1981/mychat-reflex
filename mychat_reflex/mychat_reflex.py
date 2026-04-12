"""
Super Chat - Advanced ChatGPT-like Application
Built with Reflex Framework (2026)
"""

import reflex as rx

from .pages.main import main_page
from .state.chat_state import ChatState  # noqa: F401 - imported for state registration


def index() -> rx.Component:
    """Main application entry point."""
    return main_page()


app = rx.App(
    style={
        "font_family": "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    },
    stylesheets=[
        "/styles.css",  # Custom scrollbar styles
    ],
)
app.add_page(index, title="Super Chat 2")
