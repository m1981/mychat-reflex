# mychat_reflex/mychat_reflex.py
import logging
import sys
import os
import reflex as rx
from dotenv import load_dotenv  # 1. ADD THIS IMPORT

from .pages.main import main_page

# 1. ADD THESE IMPORTS FOR DEPENDENCY INJECTION
from .core.di import AppContainer
from .infrastructure.llm_adapters import AnthropicAdapter

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
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


# ============================================================================
# 2. ADD THE COMPOSITION ROOT (Dependency Injection Wiring)
# ============================================================================
def initialize_dependencies():
    """Wire up the application dependencies before starting."""

    # 2. EXPLICITLY LOAD THE .env FILE
    load_dotenv()
    logging.info("✅ Loaded environment variables from .env file.")

    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not api_key:
        logging.error("❌ ANTHROPIC_API_KEY is missing from environment variables!")

    # Instantiate the concrete adapter
    anthropic_adapter = AnthropicAdapter(api_key=api_key, model="claude-sonnet-4-5")

    # Register it with the Service Locator
    AppContainer.register_llm_service(anthropic_adapter)
    logging.info("✅ Dependencies initialized and registered in AppContainer.")


# 3. RUN THE INITIALIZATION
initialize_dependencies()


# ============================================================================
# REFLEX APP SETUP
# ============================================================================
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
