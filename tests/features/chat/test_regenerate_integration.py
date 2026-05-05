"""
Integration tests for the regenerate message flow.

Tests the complete flow from UI action -> State -> Use Case -> Database.
"""

import pytest
from sqlmodel import Session, select
from uuid import uuid4

from mychat_reflex.features.chat.models import Message, Conversation
from mychat_reflex.features.chat.use_cases import PrepRegenerationUseCase


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session."""
    from mychat_reflex.core.database import DatabaseConfig
    from sqlmodel import create_engine, Session
    
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    
    # Create tables
    from mychat_reflex.features.chat.models import Message, Conversation, ChatFolder
    Message.metadata.create_all(engine)
    Conversation.metadata.create_all(engine)
    ChatFolder.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


def test_prep_regeneration_truncates_correctly(session: Session):
    """Test that PrepRegenerationUseCase correctly truncates conversation history."""
    
    # Setup: Create a conversation with 5 messages
    conv_id = "test-conv"
    conversation = Conversation(id=conv_id, title="Test Chat")
    session.add(conversation)
    
    msg1 = Message(id=str(uuid4()), conversation_id=conv_id, role="user", content="Hello")
    msg2 = Message(id=str(uuid4()), conversation_id=conv_id, role="assistant", content="Hi there")
    msg3 = Message(id=str(uuid4()), conversation_id=conv_id, role="user", content="How are you?")
    msg4 = Message(id=str(uuid4()), conversation_id=conv_id, role="assistant", content="I'm good")
    msg5 = Message(id=str(uuid4()), conversation_id=conv_id, role="user", content="Great!")
    
    session.add_all([msg1, msg2, msg3, msg4, msg5])
    session.commit()
    
    # Execute: Regenerate from msg3 (should delete msg4 and msg5)
    use_case = PrepRegenerationUseCase()
    new_ai_msg_id, prompt_text, truncated_history = use_case.execute(
        session, conv_id, msg3.id
    )
    
    # Assert: Check the results
    assert prompt_text == "How are you?"
    assert len(truncated_history) == 3  # msg1, msg2, msg3
    assert truncated_history[0].id == msg1.id
    assert truncated_history[1].id == msg2.id
    assert truncated_history[2].id == msg3.id
    
    # Assert: Check database state
    remaining_messages = session.exec(
        select(Message).where(Message.conversation_id == conv_id)
    ).all()
    
    # Should have: msg1, msg2, msg3, and the new AI placeholder
    assert len(remaining_messages) == 4
    message_ids = {m.id for m in remaining_messages}
    assert msg1.id in message_ids
    assert msg2.id in message_ids
    assert msg3.id in message_ids
    assert new_ai_msg_id in message_ids
    
    # msg4 and msg5 should be deleted
    assert msg4.id not in message_ids
    assert msg5.id not in message_ids
    
    # The new AI message should be empty
    new_msg = session.get(Message, new_ai_msg_id)
    assert new_msg is not None
    assert new_msg.role == "assistant"
    assert new_msg.content == ""


def test_prep_regeneration_from_assistant_message(session: Session):
    """Test regenerating from an assistant message."""
    
    conv_id = "test-conv-2"
    conversation = Conversation(id=conv_id, title="Test Chat 2")
    session.add(conversation)
    
    msg1 = Message(id=str(uuid4()), conversation_id=conv_id, role="user", content="Question")
    msg2 = Message(id=str(uuid4()), conversation_id=conv_id, role="assistant", content="Answer")
    msg3 = Message(id=str(uuid4()), conversation_id=conv_id, role="user", content="Follow up")
    
    session.add_all([msg1, msg2, msg3])
    session.commit()
    
    # Execute: Regenerate from msg2 (assistant message)
    use_case = PrepRegenerationUseCase()
    new_ai_msg_id, prompt_text, truncated_history = use_case.execute(
        session, conv_id, msg2.id
    )
    
    # Assert: Should use the previous user message as prompt
    assert prompt_text == "Question"
    assert len(truncated_history) == 1  # Only msg1
    assert truncated_history[0].id == msg1.id
    
    # Assert: msg2 and msg3 should be deleted
    remaining_messages = session.exec(
        select(Message).where(Message.conversation_id == conv_id)
    ).all()
    
    assert len(remaining_messages) == 2  # msg1 + new AI placeholder
    message_ids = {m.id for m in remaining_messages}
    assert msg1.id in message_ids
    assert new_ai_msg_id in message_ids


def test_prep_regeneration_no_destructive_action(session: Session):
    """Test regenerating the last message (non-destructive)."""
    
    conv_id = "test-conv-3"
    conversation = Conversation(id=conv_id, title="Test Chat 3")
    session.add(conversation)
    
    msg1 = Message(id=str(uuid4()), conversation_id=conv_id, role="user", content="Hello")
    msg2 = Message(id=str(uuid4()), conversation_id=conv_id, role="assistant", content="Hi")
    
    session.add_all([msg1, msg2])
    session.commit()
    
    # Execute: Regenerate from msg2 (last message, non-destructive)
    use_case = PrepRegenerationUseCase()
    new_ai_msg_id, prompt_text, truncated_history = use_case.execute(
        session, conv_id, msg2.id
    )
    
    # Assert
    assert prompt_text == "Hello"
    assert len(truncated_history) == 1
    assert truncated_history[0].id == msg1.id
    
    # Only msg2 should be deleted
    remaining_messages = session.exec(
        select(Message).where(Message.conversation_id == conv_id)
    ).all()
    
    assert len(remaining_messages) == 2  # msg1 + new placeholder
    message_ids = {m.id for m in remaining_messages}
    assert msg1.id in message_ids
    assert new_ai_msg_id in message_ids
    assert msg2.id not in message_ids
