# mychat_reflex/mychat_reflex.py
import logging
import sys
import os
import reflex as rx
from dotenv import load_dotenv

from .pages.main import main_page
from .features.chat.state import ChatState

# IMPORTS FOR DEPENDENCY INJECTION
from .core.di import AppContainer
from .infrastructure.llm_adapters import AnthropicAdapter, OpenAIAdapter
from .core.llm_ports import ILLMService

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logging.getLogger("mychat_reflex.features.chat.state").setLevel(logging.INFO)
logging.getLogger("mychat_reflex.features.chat.use_cases").setLevel(logging.INFO)
logging.getLogger("mychat_reflex.core.llm_ports").setLevel(logging.INFO)
logging.getLogger("anthropic").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

print("=" * 80)
print("🔥 LOGGING ENABLED - You will see detailed API request logs in this console!")
print("=" * 80)


# ============================================================================
# COMPOSITION ROOT (Dependency Injection Wiring)
# ============================================================================
def initialize_dependencies():
    """Wire up the application dependencies before starting."""
    load_dotenv()
    logging.info("✅ Loaded environment variables from .env file.")

    # Define the Factory Function
    def llm_factory(model_name: str) -> ILLMService:
        """Builds the correct adapter based on the requested model string."""
        model_str = str(model_name).lower()

        if model_str.startswith(("claude", "sonnet", "opus")):
            return AnthropicAdapter(
                api_key=os.getenv("ANTHROPIC_API_KEY", ""), model=model_str
            )
        elif model_str.startswith(("gpt", "o1", "o3")):
            return OpenAIAdapter(
                api_key=os.getenv("OPENAI_API_KEY", ""), model=model_str
            )
        else:
            logging.warning(f"Unknown model '{model_str}', defaulting to Claude.")
            return AnthropicAdapter(
                api_key=os.getenv("ANTHROPIC_API_KEY", ""), model="claude-sonnet-4-5"
            )

    # Register the factory with the container
    AppContainer.register_llm_factory(llm_factory)
    logging.info("✅ Dependencies initialized. Factory ready.")


# RUN THE INITIALIZATION
initialize_dependencies()


# ============================================================================
# REFLEX APP SETUP
# ============================================================================
def index() -> rx.Component:
    """Main application entry point."""
    return main_page()


app = rx.App(
    theme=rx.theme(
        appearance="inherit",
        has_background=False,
        radius="large",
        accent_color="indigo",
    ),
    stylesheets=[
        "/styles.css",
    ],
)
app.add_page(index, title="Super Chat 2", on_load=ChatState.on_load)
