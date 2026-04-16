"""
Integration Tests for Chat Use Cases.

Architectural Note (ADR 006-V2):
These tests run in milliseconds and cost $0.00 because they use:
1. An in-memory SQLite database (via SQLModel).
2. A FakeLLMAdapter (Dependency Inversion) instead of hitting Anthropic.
"""

import pytest
from typing import AsyncGenerator, Optional
from sqlmodel import Session, SQLModel, create_engine
from uuid import uuid4

from mychat_reflex.core.llm_ports import ILLMService, LLMConfig
from mychat_reflex.features.chat.models import Message, Conversation
from mychat_reflex.features.chat.use_cases import SendMessageUseCase, LoadHistoryUseCase


# ============================================================================
# FAKES & MOCKS (The "Adapters" for our test environment)
# ============================================================================


class FakeLLMAdapter(ILLMService):
    """
    A fake LLM service that returns a predictable response instantly.
    It also records the prompt it received so we can assert against it.
    """

    def __init__(self, mock_response: str = "Hello from the Fake LLM!"):
        self.mock_response = mock_response
        self.last_received_prompt = ""
        self.last_received_config = None

    async def generate_stream(
        self, prompt: str, config: Optional[LLMConfig] = None
    ) -> AsyncGenerator[str, None]:
        # Record what the Use Case sent us
        self.last_received_prompt = prompt
        self.last_received_config = config

        # Simulate streaming by yielding word by word
        words = self.mock_response.split()
        for i, word in enumerate(words):
            # Add a space after the word, unless it's the last word
            yield word + (" " if i < len(words) - 1 else "")


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(name="session")
def session_fixture():
    """Provides a fresh, in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

    # FIX: Explicitly close the engine to prevent ResourceWarnings
    engine.dispose()


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_send_message_use_case_streams_correctly():
    """Test that the Use Case correctly orchestrates the LLM stream."""
    # 1. Arrange
    fake_llm = FakeLLMAdapter(mock_response="I am a fast test.")
    use_case = SendMessageUseCase(llm_service=fake_llm)

    # 2. Act
    chunks = []
    async for chunk in use_case.execute(
        conversation_id="test-conv-1",
        user_message="Who are you?",
        history=[],
        config=LLMConfig(temperature=0.5),
    ):
        chunks.append(chunk)

    full_response = "".join(chunks)

    # 3. Assert
    assert full_response == "I am a fast test."
    assert fake_llm.last_received_config.temperature == 0.5
    assert "User: Who are you?" in fake_llm.last_received_prompt


@pytest.mark.asyncio
async def test_send_message_use_case_formats_history():
    """Test that the Use Case correctly formats previous messages into the prompt."""
    # 1. Arrange
    fake_llm = FakeLLMAdapter()
    use_case = SendMessageUseCase(llm_service=fake_llm)

    history = [
        Message(id="1", conversation_id="c1", role="user", content="Ping"),
        Message(id="2", conversation_id="c1", role="assistant", content="Pong"),
    ]

    # 2. Act
    # We just consume the generator to trigger the prompt building
    async for _ in use_case.execute(
        conversation_id="c1", user_message="Ping again", history=history
    ):
        pass

    # 3. Assert
    prompt = fake_llm.last_received_prompt
    assert "User: Ping" in prompt
    assert "Assistant: Pong" in prompt
    assert "User: Ping again" in prompt


# 1. Add the asyncio decorator
@pytest.mark.asyncio
async def test_load_history_use_case(session: Session):  # 2. Make the test async
    """Test that the Use Case correctly fetches and orders messages from the DB."""
    # 1. Arrange
    conv_id = str(uuid4())
    other_conv_id = str(uuid4())

    # Create parent conversations
    session.add(Conversation(id=conv_id, title="Target Chat"))
    session.add(Conversation(id=other_conv_id, title="Other Chat"))

    # Add messages to target conversation
    msg1 = Message(
        id=str(uuid4()), conversation_id=conv_id, role="user", content="First"
    )
    msg2 = Message(
        id=str(uuid4()), conversation_id=conv_id, role="assistant", content="Second"
    )

    # Add message to a DIFFERENT conversation (should not be loaded)
    msg3 = Message(
        id=str(uuid4()),
        conversation_id=other_conv_id,
        role="user",
        content="Wrong Chat",
    )

    session.add_all([msg1, msg2, msg3])
    session.commit()

    # 2. Act
    use_case = LoadHistoryUseCase()
    # 3. ADD AWAIT HERE!
    loaded_messages = await use_case.execute(session=session, conversation_id=conv_id)

    # 3. Assert
    assert len(loaded_messages) == 2
    assert loaded_messages[0].content == "First"
    assert loaded_messages[1].content == "Second"

    # Ensure we didn't load the message from the other chat
    for msg in loaded_messages:
        assert msg.content != "Wrong Chat"
