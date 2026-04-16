"""
Dependency Injection Container (Service Locator).

Architectural Note:
This file lives in the `core`. It MUST NOT import anything from `infrastructure`.
The Composition Root (mychat_reflex.py) or the Test Suite is responsible for
calling `register_llm_service` with the concrete adapter.
"""

import logging
from typing import Optional
from mychat_reflex.core.llm_ports import ILLMService

logger = logging.getLogger(__name__)


class AppContainer:
    """Service Locator for Dependency Injection."""

    _llm_service: Optional[ILLMService] = None

    @classmethod
    def register_llm_service(cls, service: ILLMService):
        """
        Register the concrete LLM service.
        Called at app startup (mychat_reflex.py) or during test setup.
        """
        cls._llm_service = service
        logger.info(
            f"[AppContainer] ✅ Registered LLM Service: {type(service).__name__}"
        )

    @classmethod
    def resolve_llm_service(cls) -> ILLMService:
        """
        Resolve the LLM service for use in Use Cases or State.
        """
        if cls._llm_service is None:
            logger.error(
                "[AppContainer] ❌ Attempted to resolve LLM Service before initialization!"
            )
            raise RuntimeError(
                "LLM Service not initialized in AppContainer. Call register_llm_service first."
            )

        return cls._llm_service

    @classmethod
    def clear(cls):
        """Clear the container (useful for test teardown)."""
        cls._llm_service = None
