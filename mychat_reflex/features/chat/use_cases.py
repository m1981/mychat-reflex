"""
Chat Use Cases - Pure Business Logic.

This module contains use cases for the chat feature:
- SendMessageUseCase: Orchestrates sending a message and streaming AI response
- LoadHistoryUseCase: Loads conversation history from database

IMPORTANT: Use cases are PURE business logic.
- They depend on ILLMService interface (Clean Architecture)
- They do NOT handle rx.session() - that's the State's responsibility
- They do NOT handle UI updates - that's the State's responsibility

Migrated from src/features/chat/use_cases/ (Phase 3, Task 3.1)
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
    """
    Orchestrates sending a message and streaming AI response.

    This use case:
    1. Streams LLM response chunks
    2. Remains pure business logic (no database, no UI)
    3. Depends on ILLMService interface (Clean Architecture)

    IMPORTANT: This does NOT handle rx.session() - that's the State's job!
    The caller (ChatState) must handle database persistence.
    """

    def __init__(self, llm_service: ILLMService):
        """
        Initialize use case with LLM service.

        Args:
            llm_service: LLM service implementation (Anthropic, OpenAI, etc.)
        """
        self.llm = llm_service
        logger.info("[SendMessageUseCase] Initialized")

    async def execute(
        self,
        conversation_id: str,
        user_message: str,
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
        logger.debug(f"[SendMessageUseCase] User message: {user_message[:50]}...")

        # Stream from LLM service
        chunk_count = 0
        async for chunk in self.llm.generate_stream(
            prompt=user_message,
            config=config,
        ):
            chunk_count += 1
            if chunk_count == 1:
                logger.info("[SendMessageUseCase] First chunk received from LLM")
            yield chunk

        logger.info(f"[SendMessageUseCase] Completed. Total chunks: {chunk_count}")


class LoadHistoryUseCase:
    """
    Load conversation history from database.

    This use case:
    1. Queries messages for a conversation
    2. Returns them in chronological order
    3. Uses rx.session() directly (short-lived!)

    IMPORTANT: This opens and closes rx.session() immediately.
    Do NOT hold the session during long operations.
    """

    async def execute(self, conversation_id: str) -> List[Message]:
        """
        Load all messages for a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            List of messages in chronological order

        Example:
            ```python
            use_case = LoadHistoryUseCase()
            messages = await use_case.execute("conv-123")
            for msg in messages:
                print(f"{msg.role}: {msg.content}")
            ```
        """
        logger.info(f"[LoadHistoryUseCase] Loading history for: {conversation_id}")

        # Open session, query, close immediately
        with rx.session() as session:
            messages = (
                session.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
                .all()
            )

            logger.info(f"[LoadHistoryUseCase] Loaded {len(messages)} messages")
            return messages
