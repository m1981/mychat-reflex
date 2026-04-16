import pytest
from unittest.mock import AsyncMock, patch
from mychat_reflex.core.llm_ports import LLMConfig
from mychat_reflex.infrastructure.llm_adapters import AnthropicAdapter


@pytest.fixture
def mock_anthropic_client():
    """Creates a mock Anthropic client that yields a fake stream."""
    # FIX: Patch the actual anthropic library, not our local module
    with patch("anthropic.AsyncAnthropic") as MockClient:
        mock_instance = MockClient.return_value

        # Mock the async context manager for the stream
        mock_stream_context = AsyncMock()
        mock_instance.messages.stream.return_value = mock_stream_context

        # Mock the actual text_stream generator
        async def fake_text_stream():
            yield "Mocked "
            yield "Response"

        mock_stream_context.__aenter__.return_value.text_stream = fake_text_stream()

        yield mock_instance


@pytest.mark.asyncio
async def test_anthropic_adapter_standard_request(mock_anthropic_client):
    """Test that standard config maps to the correct Anthropic kwargs."""
    adapter = AnthropicAdapter(api_key="fake", model="claude-sonnet-4.5")
    config = LLMConfig(temperature=0.5, enable_reasoning=False)

    # Consume the stream
    chunks = [chunk async for chunk in adapter.generate_stream("Hello", config)]

    assert "".join(chunks) == "Mocked Response"

    # Verify the exact payload sent to Anthropic
    mock_anthropic_client.messages.stream.assert_called_once()
    call_kwargs = mock_anthropic_client.messages.stream.call_args.kwargs

    assert call_kwargs["model"] == "claude-sonnet-4.5"
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]
    assert "thinking" not in call_kwargs


@pytest.mark.asyncio
async def test_anthropic_adapter_reasoning_request(mock_anthropic_client):
    """Test that enable_reasoning injects the thinking block correctly."""
    # Note: Reasoning only works on claude-sonnet-4 models
    adapter = AnthropicAdapter(api_key="fake", model="claude-sonnet-4.5")
    config = LLMConfig(enable_reasoning=True, reasoning_budget=4000)

    # Consume the stream
    async for _ in adapter.generate_stream("Solve this math problem", config):
        pass

    call_kwargs = mock_anthropic_client.messages.stream.call_args.kwargs

    # Verify the thinking block was injected
    assert "thinking" in call_kwargs
    assert call_kwargs["thinking"]["type"] == "enabled"
    assert call_kwargs["thinking"]["budget_tokens"] == 4000
