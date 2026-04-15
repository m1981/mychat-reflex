# mychat_reflex/core/llm_ports.py
from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncGenerator, Optional
from pydantic import BaseModel


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class LLMConfig(BaseModel):
    temperature: float = 0.7
    enable_reasoning: bool = False
    reasoning_budget: Optional[int] = None


class ILLMService(ABC):
    @abstractmethod
    async def generate_stream(
        self, prompt: str, config: Optional[LLMConfig] = None
    ) -> AsyncGenerator[str, None]:
        pass
