import pytest
from unittest.mock import AsyncMock, patch
from mychat_reflex.core.llm_ports import LLMConfig
from mychat_reflex.infrastructure.llm_adapters import AnthropicAdapter, OpenAIAdapter

# ============================================================================
# TEST DOUBLES (FIXTURES)
# ============================================================================


@pytest.fixture
def mock_anthropic_client():
    """
    MOCK STRATEGY:
    Anthropic uses `async with`. We must mock the `__aenter__` method to
    yield our fake async generator.
    """
    with patch("anthropic.AsyncAnthropic") as MockClient:
        mock_instance = MockClient.return_value

        # Mock the async context manager for the stream
        mock_stream_context = AsyncMock()
        mock_instance.messages.stream.return_value = mock_stream_context

        # Mock the actual text_stream generator
        async def fake_text_stream():
            yield "Mocked "
            yield "Response"

        # Attach the generator to the context manager's entry point
        mock_stream_context.__aenter__.return_value.text_stream = fake_text_stream()

        yield mock_instance


@pytest.fixture
def mock_openai_client():
    """
    FAKE STRATEGY:
    OpenAI returns an async generator directly. unittest.mock fails here.
    We build a pure Python Fake to capture kwargs and yield fake chunks.
    """

    class FakeDelta:
        content = "Mocked OpenAI"

    class FakeChoice:
        delta = FakeDelta()

    class FakeChunk:
        choices = [FakeChoice()]

    # 2. Define the Fake Client structure
    class FakeCompletions:
        # We store kwargs here so our tests can assert against them!
        last_kwargs = {}

        async def create(self, *args, **kwargs):
            self.last_kwargs.update(kwargs)

            async def fake_stream():
                yield FakeChunk()

            return fake_stream()

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeAsyncOpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = FakeChat()

    # Inject our Fake into the module namespace
    fake_client = FakeAsyncOpenAI()
    with patch("openai.AsyncOpenAI", return_value=fake_client):
        yield fake_client


# ============================================================================
# ANTHROPIC TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_anthropic_adapter_standard_request(mock_anthropic_client):
    """Test that standard config maps to the correct Anthropic kwargs."""
    adapter = AnthropicAdapter(api_key="fake", model="claude-sonnet-4-5")
    config = LLMConfig(temperature=0.5, enable_reasoning=False)

    # ACT: Consume the stream
    chunks = [chunk async for chunk in adapter.generate_stream("Hello", config)]

    # ASSERT OUTPUT
    assert "".join(chunks) == "Mocked Response"

    # ASSERT INPUT (Behavior verification via Mock)
    mock_anthropic_client.messages.stream.assert_called_once()
    call_kwargs = mock_anthropic_client.messages.stream.call_args.kwargs

    assert call_kwargs["model"] == "claude-sonnet-4-5"
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]
    assert "thinking" not in call_kwargs


@pytest.mark.asyncio
async def test_anthropic_adapter_reasoning_request(mock_anthropic_client):
    """Test that enable_reasoning injects the thinking block correctly."""
    adapter = AnthropicAdapter(api_key="fake", model="claude-sonnet-4-5")
    config = LLMConfig(enable_reasoning=True, reasoning_budget=4000)

    # ACT
    async for _ in adapter.generate_stream("Solve this math problem", config):
        pass

    # ASSERT INPUT
    call_kwargs = mock_anthropic_client.messages.stream.call_args.kwargs
    assert "thinking" in call_kwargs
    assert call_kwargs["thinking"]["type"] == "enabled"
    assert call_kwargs["thinking"]["budget_tokens"] == 4000


@pytest.mark.asyncio
async def test_anthropic_adapter_error_handling(mock_anthropic_client):
    """Test that API errors are properly caught and re-raised."""
    # ARRANGE: Force the mock to raise an exception
    mock_anthropic_client.messages.stream.side_effect = Exception(
        "Anthropic API is down!"
    )

    adapter = AnthropicAdapter(api_key="fake")
    config = LLMConfig()

    # ACT & ASSERT
    with pytest.raises(Exception, match="Anthropic API is down!"):
        async for _ in adapter.generate_stream("Hello", config):
            pass


# ============================================================================
# OPENAI TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_openai_adapter_standard_request(mock_openai_client):
    """Test that standard config maps to the correct OpenAI kwargs."""
    adapter = OpenAIAdapter(api_key="fake", model="gpt-4o")
    config = LLMConfig(temperature=0.8)

    # ACT: Consume the stream
    chunks = [chunk async for chunk in adapter.generate_stream("Hello", config)]

    # ASSERT OUTPUT
    assert "".join(chunks) == "Mocked OpenAI"

    # ASSERT INPUT (State verification via Fake)
    call_kwargs = mock_openai_client.chat.completions.last_kwargs

    assert call_kwargs["model"] == "gpt-4o"
    assert call_kwargs["temperature"] == 0.8
    assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]
    assert call_kwargs["stream"] is True


@pytest.mark.asyncio
async def test_openai_adapter_o1_reasoning_request(mock_openai_client):
    """Test that o1 models strip temperature and add reasoning_effort."""
    adapter = OpenAIAdapter(api_key="fake", model="o1-mini")
    config = LLMConfig(enable_reasoning=True, reasoning_budget=5000)

    # ACT
    async for _ in adapter.generate_stream("Solve this", config):
        pass

    # ASSERT INPUT
    call_kwargs = mock_openai_client.chat.completions.last_kwargs
    assert "temperature" not in call_kwargs  # o1 forbids temperature
    assert call_kwargs["reasoning_effort"] == "medium"
