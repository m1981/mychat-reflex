from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    # Note: We do NOT add "developer" here. As per ADR 010,
    # the Domain stays pure. The Adapter handles the "developer" translation.


# --- ADR 008: LLM Configuration ---
class LLMConfig(BaseModel):
    """Generic configuration for LLM generation."""

    temperature: float = 0.7
    enable_reasoning: bool = False
    reasoning_budget: Optional[int] = None


# --- ADR 009: Polymorphic Message Content ---
class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImagePart(BaseModel):
    type: Literal["image"] = "image"
    base64_data: str
    mime_type: str  # e.g., "image/jpeg", "image/png"


class DocumentPart(BaseModel):
    type: Literal["document"] = "document"
    base64_data: str
    mime_type: str  # e.g., "application/pdf"


# Type alias for the discriminated union
ContentPart = Union[TextPart, ImagePart, DocumentPart]


class ChatMessage(BaseModel):
    """
    Domain representation of a chat message.
    Content can be a simple string (legacy/standard) or a list of polymorphic parts (multimodal).
    """

    role: Role
    content: Union[str, List[ContentPart]]


# --- RAG Entities ---
class SearchResult(BaseModel):
    """Used for RAG Search Results."""

    id: str
    text: str
    score: float
    metadata: dict = Field(default_factory=dict)
