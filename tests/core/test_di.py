import pytest
from typing import AsyncGenerator, Optional

from mychat_reflex.core.di import AppContainer
from mychat_reflex.core.llm_ports import ILLMService, LLMConfig


# ============================================================================
# TEST DOUBLES
# ============================================================================


class DummyService(ILLMService):
    """A dummy implementation of ILLMService for testing purposes."""

    async def generate_stream(
        self, prompt: str, config: Optional[LLMConfig] = None
    ) -> AsyncGenerator[str, None]:
        yield "dummy"


# ============================================================================
# FIXTURES (Rule 2: Keep Tests ISOLATED)
# ============================================================================


@pytest.fixture(autouse=True)
def isolate_container():
    """
    Runs before and after EVERY test to ensure global state is wiped clean.
    This guarantees tests can run in any order without side effects.
    """
    AppContainer.clear()
    yield
    AppContainer.clear()


# ============================================================================
# TESTS (Rule 1: Readable, Rule 5: Behavior-focused)
# ============================================================================


def test_should_raise_error_when_resolving_uninitialized_factory():
    """Test that resolving before registering raises a clear error."""
    # Given
    # (Container is already cleared by the fixture)

    # When / Then
    with pytest.raises(RuntimeError) as exc_info:
        AppContainer.resolve_llm_service("gpt-4o")

    assert "LLM Factory not initialized" in str(exc_info.value)


def test_should_resolve_service_using_registered_factory():
    """Test successful registration and resolution via the factory pattern."""
    # Given
    dummy_instance = DummyService()

    def mock_factory(model_name: str) -> ILLMService:
        return dummy_instance

    AppContainer.register_llm_factory(mock_factory)

    # When
    resolved_service = AppContainer.resolve_llm_service("any-model")

    # Then
    assert resolved_service is dummy_instance  # Must be the exact same instance


def test_should_raise_error_after_container_is_cleared():
    """Test that clear() successfully removes the registered factory."""

    # Given
    def mock_factory(model_name: str) -> ILLMService:
        return DummyService()

    AppContainer.register_llm_factory(mock_factory)

    # When
    AppContainer.clear()

    # Then
    with pytest.raises(RuntimeError) as exc_info:
        AppContainer.resolve_llm_service("gpt-4o")

    assert "LLM Factory not initialized" in str(exc_info.value)
