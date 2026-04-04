from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional
from .entities import ChatMessage, SearchResult


class ILLMService(ABC):
    @abstractmethod
    async def generate_stream(
            self,
            messages: List[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        """Yields text chunks from the LLM (OpenAI, Anthropic, Local)."""
        pass


class IVectorStore(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Searches ChromaDB or Voyage AI for relevant context."""
        pass


class IConversationRepo(ABC):
    @abstractmethod
    async def save_message(self, conversation_id: str, role: Role, content: str) -> str:
        """Saves a message and returns its ID."""
        pass

    @abstractmethod
    async def get_history(self, conversation_id: str) -> List[ChatMessage]:
        """Retrieves conversation history for the LLM."""
        pass