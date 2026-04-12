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
        logger.info(
            f"[SendMessageUseCase] Executing for conversation: {conversation_id}"
        )

        # ✅ CRITICAL FIX: Format the history so the AI has memory
        transcript = ""
        for msg in history:
            speaker = "User" if msg.is_user else "Assistant"
            transcript += f"{speaker}: {msg.content}\n\n"

        # Append the current message
        transcript += f"User: {user_message}\n\nAssistant:"

        # Stream from LLM service using the full transcript
        chunk_count = 0
        async for chunk in self.llm.generate_stream(
            prompt=transcript,
            config=config,
        ):
            chunk_count += 1
            if chunk_count == 1:
                logger.info("[SendMessageUseCase] First chunk received from LLM")
            yield chunk

        logger.info(f"[SendMessageUseCase] Completed. Total chunks: {chunk_count}")


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
