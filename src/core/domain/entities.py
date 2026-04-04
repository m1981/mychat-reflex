from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# Used for RAG Search Results
class SearchResult(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict = Field(default_factory=dict)

# Used to pass message history to the LLM
class ChatMessage(BaseModel):
    role: Role
    content: str