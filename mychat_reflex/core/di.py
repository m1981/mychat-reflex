"""
Dependency Injection Container (Factory Pattern).

Architectural Note:
This file lives in the `core`. It MUST NOT import anything from `infrastructure`.
It holds a factory function registered by the Composition Root, ensuring that
every user request gets a fresh, thread-safe instance of the LLM adapter.
"""

import logging
from typing import Callable, Optional
from mychat_reflex.core.llm_ports import ILLMService

logger = logging.getLogger(__name__)


class AppContainer:
    """Service Locator / Factory for Dependency Injection."""

    _llm_factory: Optional[Callable[[str], ILLMService]] = None

    @classmethod
    def register_llm_factory(cls, factory_func: Callable[[str], ILLMService]):
        """
        Register the factory function that builds concrete LLM services.
        Called at app startup (mychat_reflex.py).
        """
        cls._llm_factory = factory_func
        logger.info("[AppContainer] ✅ Registered LLM Factory Function.")

    @classmethod
    def resolve_llm_service(cls, model_name: str) -> ILLMService:
        """
        Build and return a fresh LLM service for the requested model.
        This ensures multi-user thread safety in Reflex.
        """
        if cls._llm_factory is None:
            logger.error(
                "[AppContainer] ❌ Attempted to resolve LLM Service before initialization!"
            )
            raise RuntimeError(
                "LLM Factory not initialized in AppContainer. Call register_llm_factory first."
            )

        return cls._llm_factory(model_name)

    @classmethod
    def clear(cls):
        """Clear the container (useful for test teardown)."""
        cls._llm_factory = None
