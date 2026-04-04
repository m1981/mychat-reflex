# File: src/core/di.py
import os
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.session import get_db
from src.infrastructure.database.conversation_repo import SQLAlchemyConversationRepo
from src.infrastructure.vector_store.mock_adapter import MockVectorStore
from src.infrastructure.llm.anthropic_adapter import AnthropicAdapter
from src.features.chat.domain.services.prompt_builder import RAGPromptBuilder
from src.features.chat.use_cases.send_message import SendMessageUseCase

# --- Providers ---


def get_conversation_repo(
    session: AsyncSession = Depends(get_db),
) -> SQLAlchemyConversationRepo:
    return SQLAlchemyConversationRepo(session)


def get_vector_store() -> MockVectorStore:
    return MockVectorStore()


def get_llm_service() -> AnthropicAdapter:
    api_key = os.getenv("ANTHROPIC_API_KEY", "your-api-key-here")
    return AnthropicAdapter(api_key=api_key, model="claude-3-5-sonnet-20241022")


def get_prompt_builder() -> RAGPromptBuilder:
    return RAGPromptBuilder()


# --- Main Use Case Injection ---


def get_send_message_use_case(
    repo: SQLAlchemyConversationRepo = Depends(get_conversation_repo),
    vector_store: MockVectorStore = Depends(get_vector_store),
    llm: AnthropicAdapter = Depends(get_llm_service),
    prompt_builder: RAGPromptBuilder = Depends(get_prompt_builder),
) -> SendMessageUseCase:
    """
    Wires together the Clean Architecture Use Case.
    FastAPI will automatically resolve all dependencies in the tree.
    """
    return SendMessageUseCase(
        conversation_repo=repo,
        vector_store=vector_store,
        llm_service=llm,
        prompt_builder=prompt_builder,
    )
