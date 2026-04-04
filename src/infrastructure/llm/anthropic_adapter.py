import logging
from typing import AsyncGenerator, List, Optional, Dict, Any
from anthropic import AsyncAnthropic
from src.core.domain.interfaces import ILLMService
from src.core.domain.entities import (
    ChatMessage,
    LLMConfig,
    Role,
    TextPart,
    ImagePart,
    DocumentPart,
)

logger = logging.getLogger(__name__)


class AnthropicAdapter(ILLMService):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate_stream(
        self, messages: List[ChatMessage], config: Optional[LLMConfig] = None
    ) -> AsyncGenerator[str, None]:
        config = config or LLMConfig()

        logger.info(
            f"[AnthropicAdapter] Starting stream generation with model: {self.model}"
        )
        logger.debug(f"[AnthropicAdapter] Received {len(messages)} messages")
        logger.debug(
            f"[AnthropicAdapter] Config: temperature={config.temperature}, reasoning={config.enable_reasoning}"
        )

        # Anthropic requires system messages to be separate from the messages array
        system_content = None
        anthropic_messages = []

        for msg in messages:
            # Extract system message separately
            if msg.role == Role.SYSTEM:
                if isinstance(msg.content, str):
                    system_content = msg.content
                else:
                    # If system message has multimodal content, convert to text
                    text_parts = [
                        p.text for p in msg.content if isinstance(p, TextPart)
                    ]
                    system_content = "\n".join(text_parts)
                continue

            # Format user/assistant messages
            role = msg.role.value  # "user" or "assistant"

            # Handle polymorphic content
            if isinstance(msg.content, str):
                formatted_content = msg.content
            else:
                # Multimodal content
                formatted_content = []
                for part in msg.content:
                    if isinstance(part, TextPart):
                        formatted_content.append({"type": "text", "text": part.text})
                    elif isinstance(part, ImagePart):
                        formatted_content.append(
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": part.mime_type,
                                    "data": part.base64_data,
                                },
                            }
                        )
                    elif isinstance(part, DocumentPart):
                        # Anthropic supports PDF documents
                        formatted_content.append(
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": part.mime_type,
                                    "data": part.base64_data,
                                },
                            }
                        )

            anthropic_messages.append({"role": role, "content": formatted_content})

        # Build API call parameters
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": 4096,
        }

        # Add system message if present
        if system_content:
            kwargs["system"] = system_content
            logger.debug(
                f"[AnthropicAdapter] System message length: {len(system_content)} chars"
            )

        # Add temperature (Anthropic supports it for all models)
        kwargs["temperature"] = config.temperature

        # Handle extended thinking (Claude 3.7 Sonnet feature)
        if config.enable_reasoning and "claude-3-7-sonnet" in self.model:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": config.reasoning_budget or 2000,
            }
            logger.debug("[AnthropicAdapter] Extended thinking enabled")

        logger.info(
            f"[AnthropicAdapter] Calling Anthropic API with {len(anthropic_messages)} messages"
        )
        logger.debug(f"[AnthropicAdapter] API kwargs: {list(kwargs.keys())}")

        try:
            # Stream the response - messages.stream() is already a streaming context manager
            chunk_count = 0
            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    chunk_count += 1
                    if chunk_count == 1:
                        logger.info("[AnthropicAdapter] First chunk received")
                    yield text

            logger.info(
                f"[AnthropicAdapter] Stream completed. Total chunks: {chunk_count}"
            )

        except Exception as e:
            logger.error(
                f"[AnthropicAdapter] Error during streaming: {type(e).__name__}: {str(e)}"
            )
            raise
