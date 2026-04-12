"""
Chat Use Cases - Pure Business Logic.
"""

import logging
from typing import AsyncGenerator, List, Optional
import reflex as rx

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
        history: List[Message],  # ✅ CRITICAL FIX: Added history parameter
        config: Optional[LLMConfig] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Execute the use case - stream AI response.

        Args:
            conversation_id: ID of the conversation
            user_message: User's message text
            config: Optional LLM configuration

        Yields:
            Text chunks from the LLM as they arrive

        Example:
            ```python
            use_case = SendMessageUseCase(llm_service)
            async for chunk in use_case.execute("conv-123", "Hello"):
                print(chunk, end="")
            ```
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

        # ✅ CRITICAL FIX: Format the history so the AI has memory
        transcript = ""
        for i, msg in enumerate(history):
            speaker = "User" if msg.is_user else "Assistant"
            transcript += f"{speaker}: {msg.content}\n\n"
            logger.debug(
                f"[SendMessageUseCase] History[{i}] ({speaker}): {msg.content[:50]}..."
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

    async def execute(self, conversation_id: str) -> List[Message]:
        logger.info(f"[LoadHistoryUseCase] Loading history for: {conversation_id}")

        # Open session, query, close immediately
        with rx.session() as session:
            messages = (
                session.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
                .all()
            )

            # CRITICAL FIX 2: Detach objects from the session before it closes!
            # This prevents DetachedInstanceError crashes in the UI.
            session.expunge_all()

            logger.info(f"[LoadHistoryUseCase] Loaded {len(messages)} messages")
            return messages
