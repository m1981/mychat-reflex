"""
Unit tests for SendMessageUseCase.
"""

import pytest
from typing import AsyncGenerator, Optional
from mychat_reflex.core.llm_ports import ILLMService, LLMConfig
from mychat_reflex.features.chat.models import Message

# ============================================================================
# TEST DOUBLES (Fake LLM)
# ============================================================================


class FakeLLM(ILLMService):
    """Fake LLM for testing - returns predictable responses."""

    def __init__(self, response: str = "Test AI response"):
        self.response = response
        self.last_prompt: Optional[str] = None
        self.last_config: Optional[LLMConfig] = None
        self.call_count = 0

    async def generate_stream(
        self,
        prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> AsyncGenerator[str, None]:
        self.last_prompt = prompt
        self.last_config = config
        self.call_count += 1

        words = self.response.split()
        for word in words:
            yield word + " "


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_send_message_streams_llm_response():
    """Test that SendMessageUseCase streams LLM response chunks."""
    from mychat_reflex.features.chat.use_cases import SendMessageUseCase

    fake_llm = FakeLLM(response="Hello world from AI")
    use_case = SendMessageUseCase(llm_service=fake_llm)

    chunks = []
    # ARCHITECT FIX: Added empty history list
    async for chunk in use_case.execute(
        conversation_id="test-conv-123", user_message="Test prompt", history=[]
    ):
        chunks.append(chunk)

    assert len(chunks) == 4
    assert "".join(chunks).strip() == "Hello world from AI"
    assert fake_llm.call_count == 1
    # ARCHITECT FIX: Expect the formatted transcript, not just the raw prompt
    assert fake_llm.last_prompt == "User: Test prompt\n\nAssistant:"


@pytest.mark.asyncio
async def test_send_message_formats_history_correctly():
    """Test that previous messages are included in the prompt transcript."""
    from mychat_reflex.features.chat.use_cases import SendMessageUseCase

    fake_llm = FakeLLM()
    use_case = SendMessageUseCase(llm_service=fake_llm)

    # Create fake history
    history = [
        Message(id="1", conversation_id="c1", role="user", content="Hi"),
        Message(id="2", conversation_id="c1", role="assistant", content="Hello"),
    ]

    async for _ in use_case.execute("c1", "How are you?", history=history):
        pass

    expected_transcript = (
        "User: Hi\n\nAssistant: Hello\n\nUser: How are you?\n\nAssistant:"
    )
    assert fake_llm.last_prompt == expected_transcript


@pytest.mark.asyncio
async def test_send_message_passes_config_to_llm():
    """Test that LLMConfig is passed to the LLM service."""
    from mychat_reflex.features.chat.use_cases import SendMessageUseCase

    fake_llm = FakeLLM()
    use_case = SendMessageUseCase(llm_service=fake_llm)

    async for _ in use_case.execute("test-conv", "Test", history=[]):
        pass

    assert fake_llm.last_config is not None
    assert fake_llm.last_config.temperature == 0.7


@pytest.mark.asyncio
async def test_send_message_handles_empty_response():
    """Test handling of empty LLM response."""
    # Arrange
    from mychat_reflex.features.chat.use_cases import SendMessageUseCase

    fake_llm = FakeLLM(response="")
    use_case = SendMessageUseCase(llm_service=fake_llm)

    # Act
    chunks = []
    async for chunk in use_case.execute(
        conversation_id="test-conv",
        user_message="Test",
        history=[],  # ✅ CRITICAL FIX: Added empty history
    ):
        chunks.append(chunk)

    # Assert
    assert len(chunks) == 0


@pytest.mark.asyncio
async def test_send_message_preserves_clean_architecture():
    """Test that use case depends on interface, not concrete implementation."""
    # Arrange
    from mychat_reflex.features.chat.use_cases import SendMessageUseCase

    # This should work with ANY ILLMService implementation
    fake_llm = FakeLLM(response="Clean architecture works")
    use_case = SendMessageUseCase(llm_service=fake_llm)

    # Act
    result = []
    async for chunk in use_case.execute(
        conversation_id="test",
        user_message="Test clean architecture",
        history=[],  # ✅ CRITICAL FIX: Added empty history
    ):
        result.append(chunk)

    # Assert - use case doesn't care about concrete implementation
    assert len(result) > 0
    assert isinstance(fake_llm, ILLMService)
