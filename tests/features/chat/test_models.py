from datetime import datetime, timezone
from mychat_reflex.features.chat.models import Message, Conversation


def test_message_role_properties():
    """Test the is_user and is_assistant properties."""
    user_msg = Message(id="1", conversation_id="c1", role="user", content="Hi")
    ai_msg = Message(id="2", conversation_id="c1", role="assistant", content="Hello")
    sys_msg = Message(id="3", conversation_id="c1", role="system", content="Init")

    assert user_msg.is_user is True
    assert user_msg.is_assistant is False

    assert ai_msg.is_assistant is True
    assert ai_msg.is_user is False

    assert sys_msg.is_user is False
    assert sys_msg.is_assistant is False


def test_message_timestamp_formatting():
    """Test that the timestamp formats correctly for the UI."""
    # Create a specific time: March 30, 2026, 18:15:00 UTC
    dt = datetime(2026, 3, 30, 18, 15, 0, tzinfo=timezone.utc)
    msg = Message(
        id="1", conversation_id="c1", role="user", content="Hi", created_at=dt
    )

    # Should format as "06:15 PM 30 Mar 2026"
    assert msg.timestamp_formatted == "06:15 PM 30 Mar 2026"


def test_conversation_folder_property():
    """Test the is_in_folder property."""
    conv_no_folder = Conversation(id="1", title="A")
    conv_with_folder = Conversation(id="2", title="B", folder_id="folder-1")

    assert conv_no_folder.is_in_folder is False
    assert conv_with_folder.is_in_folder is True
