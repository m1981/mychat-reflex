"""
Chat Use Cases - Pure Business Logic.

Architectural Rules Applied:
- Clean Architecture: No framework imports (Reflex is completely removed).
- CQS: SendMessageUseCase is a Command (orchestrates side effects).
       LoadHistoryUseCase is a Query (reads data).
- Dependency Injection: Database sessions and LLM services are passed in.
"""

import logging
from typing import AsyncGenerator, List, Optional
from sqlmodel import Session, select
from uuid import uuid4

from mychat_reflex.core.llm_ports import ILLMService, LLMConfig
from .models import Message

logger = logging.getLogger(__name__)


# ============================================================================
# USE CASES
# ============================================================================


class SendMessageUseCase:
    """Orchestrates sending a message and streaming AI response."""

    def __init__(self, llm_service: ILLMService):
        self.llm = llm_service
        logger.info("[SendMessageUseCase] Initialized")

    async def execute(
        self,
        conversation_id: str,
        user_message: str,
        history: List[Message],
        config: Optional[LLMConfig] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Execute the use case - stream AI response.

        Args:
            conversation_id: ID of the conversation
            user_message: User's message text
            history: Previous messages in the conversation
            config: Optional LLM configuration

        Yields:
            Text chunks from the LLM as they arrive
        """
        config = config or LLMConfig(temperature=0.7)

        logger.info("=" * 80)
        logger.info("[SendMessageUseCase] 📨 EXECUTING USE CASE")
        logger.info("=" * 80)
        logger.info(f"[SendMessageUseCase] Conversation ID: {conversation_id}")
        logger.info(f"[SendMessageUseCase] User message: {user_message}")
        logger.info(f"[SendMessageUseCase] History length: {len(history)} messages")
        logger.info(f"[SendMessageUseCase] Config: {config}")
        logger.info("-" * 80)

        # Format the history so the AI has memory
        transcript = ""
        for i, msg in enumerate(history):
            speaker = "User" if msg.is_user else "Assistant"
            content = msg.content or ""
            transcript += f"{speaker}: {content}\n\n"
            logger.debug(
                f"[SendMessageUseCase] History[{i}] ({speaker}): {content[:50]}..."
            )

        # Append the current message
        transcript += f"User: {user_message}\n\nAssistant:"

        logger.info(
            f"[SendMessageUseCase] Built transcript with {len(transcript)} characters"
        )
        logger.info("[SendMessageUseCase] 🔄 Calling LLM service...")

        # Stream from LLM service using the full transcript
        chunk_count = 0
        async for chunk in self.llm.generate_stream(
            prompt=transcript,
            config=config,
        ):
            chunk_count += 1
            if chunk_count == 1:
                logger.info("[SendMessageUseCase] ✅ First chunk received from LLM")
            if chunk_count % 10 == 0:
                logger.debug(f"[SendMessageUseCase] Received chunk #{chunk_count}")
            yield chunk

        logger.info("=" * 80)
        logger.info("[SendMessageUseCase] ✅ USE CASE COMPLETED")
        logger.info("=" * 80)
        logger.info(f"[SendMessageUseCase] Total chunks: {chunk_count}")
        logger.info("=" * 80)


class LoadHistoryUseCase:
    """Load conversation history from database."""

    async def execute(self, session: Session, conversation_id: str) -> List[Message]:
        logger.info(f"[LoadHistoryUseCase] Loading history for: {conversation_id}")

        # FIX: Use modern SQLModel select() syntax
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )

        messages = session.exec(statement).all()
        return list(messages)


# Add this to the bottom of mychat_reflex/features/chat/use_cases.py



class PrepRegenerationUseCase:
    """
    Handles the business logic of truncating a conversation timeline.
    Determines which messages to delete, deletes them from the DB,
    and returns the new state.
    """

    def execute(
            self, session: Session, conversation_id: str, target_message_id: str
    ) -> tuple[str, str, list[Message]]:
        """
        Args:
            session: Database session
            conversation_id: The current chat ID
            target_message_id: The ID of the message the user clicked "regenerate" on

        Returns:
            Tuple containing:
            - new_ai_msg_id (str): The ID for the new AI placeholder
            - prompt_text (str): The user prompt to send to the LLM
            - truncated_history (list[Message]): The remaining messages before the prompt
        """
        logger.info(f"[PrepRegenerationUseCase] Preparing regeneration for msg: {target_message_id}")

        # 1. Fetch all messages in this conversation
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = list(session.exec(statement).all())

        # 2. Find the target message
        target_idx = next((i for i, m in enumerate(messages) if m.id == target_message_id), -1)
        if target_idx == -1:
            raise ValueError("Message not found in database.")

        target_msg = messages[target_idx]

        # 3. Determine the prompt and what to delete
        if target_msg.role == "assistant":
            if target_idx == 0 or messages[target_idx - 1].role != "user":
                raise ValueError("Could not find the original user prompt.")
            prompt_text = messages[target_idx - 1].content
            delete_from_idx = target_idx
        else:
            prompt_text = target_msg.content
            delete_from_idx = target_idx + 1

        # 4. Delete the alternate timeline from the database
        messages_to_delete = messages[delete_from_idx:]
        ids_to_delete = [m.id for m in messages_to_delete]

        if ids_to_delete:
            logger.info(f"[PrepRegenerationUseCase] Truncating {len(ids_to_delete)} messages from DB.")
            delete_statement = select(Message).where(Message.id.in_(ids_to_delete))
            for msg in session.exec(delete_statement).all():
                session.delete(msg)

        # 5. Create the new AI placeholder in the database
        new_ai_msg_id = str(uuid4())
        new_ai_msg = Message(
            id=new_ai_msg_id,
            conversation_id=conversation_id,
            role="assistant",
            content="",
        )
        session.add(new_ai_msg)
        session.commit()

        # 6. Return the clean data for the UI to use
        truncated_history = messages[:delete_from_idx]

        # Make copies of the data to prevent DetachedInstanceError in UI
        # This ensures the objects can be used after the session closes
        # We need to manually copy all fields because model_dump() may exclude some
        truncated_history_copies = []
        for msg in truncated_history:
            msg_copy = Message(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                model_used=msg.model_used,
                avatar_url=msg.avatar_url,
            )
            truncated_history_copies.append(msg_copy)

        return new_ai_msg_id, prompt_text, truncated_history_copies
