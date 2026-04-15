import os
import logging
from mychat_reflex.core.llm_ports import ILLMService
from mychat_reflex.infrastructure.llm_adapters import AnthropicAdapter

logger = logging.getLogger(__name__)


class AppContainer:
    """Service Locator with Lazy Initialization."""

    _llm_service: ILLMService = None

    @classmethod
    def resolve_llm_service(cls) -> ILLMService:
        # If it doesn't exist yet, build it!
        if cls._llm_service is None:
            logger.info("[AppContainer] Lazy-initializing LLM Service...")

            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if not api_key:
                logger.error(
                    "[AppContainer] ❌ ANTHROPIC_API_KEY is missing from environment!"
                )

            # Instantiate the concrete adapter
            cls._llm_service = AnthropicAdapter(
                api_key=api_key, model="claude-sonnet-4-5"
            )
            logger.info("[AppContainer] ✅ LLM Service initialized successfully.")

        return cls._llm_service
