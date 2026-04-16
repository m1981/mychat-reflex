import pytest
from mychat_reflex.core.di import AppContainer
from mychat_reflex.core.llm_ports import ILLMService, LLMConfig
from typing import AsyncGenerator, Optional


# A dummy service just for testing the container
class DummyService(ILLMService):
    async def generate_stream(
        self, prompt: str, config: Optional[LLMConfig] = None
    ) -> AsyncGenerator[str, None]:
        yield "dummy"


def test_di_container_uninitialized_raises_error():
    """Test that resolving before registering raises a clear error."""
    # Reset container state just in case
    AppContainer._llm_service = None

    with pytest.raises(RuntimeError) as exc_info:
        AppContainer.resolve_llm_service()

    assert "LLM Service not initialized" in str(exc_info.value)


def test_di_container_registers_and_resolves():
    """Test successful registration and resolution."""
    dummy = DummyService()

    AppContainer.register_llm_service(dummy)
    resolved = AppContainer.resolve_llm_service()

    assert resolved is dummy  # Must be the exact same instance
