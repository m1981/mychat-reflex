"""
Super Chat - Advanced ChatGPT-like Application
Built with Reflex Framework (2026)
"""

import logging
import sys
import reflex as rx

from .pages.main import main_page
from .features.chat.state import ChatState  # noqa: F401 - imported for state registration

# ============================================================================
# LOGGING CONFIGURATION - Make logs visible in console!
# ============================================================================

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to console
    ],
)

# Set specific loggers to INFO level to see our custom logs
logging.getLogger("mychat_reflex.features.chat.state").setLevel(logging.INFO)
logging.getLogger("mychat_reflex.features.chat.use_cases").setLevel(logging.INFO)
logging.getLogger("mychat_reflex.core.llm_ports").setLevel(logging.INFO)

# Reduce noise from other libraries
logging.getLogger("anthropic").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

print("=" * 80)
print("🔥 LOGGING ENABLED - You will see detailed API request logs in this console!")
print("=" * 80)


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
