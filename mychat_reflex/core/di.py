# mychat_reflex/core/di.py
from mychat_reflex.core.llm_ports import ILLMService


class AppContainer:
    """Simple Service Locator for Reflex States."""

    _llm_service: ILLMService = None

    @classmethod
    def register_llm_service(cls, service: ILLMService):
        cls._llm_service = service

    @classmethod
    def resolve_llm_service(cls) -> ILLMService:
        if not cls._llm_service:
            raise RuntimeError("LLM Service not initialized in AppContainer")
        return cls._llm_service
