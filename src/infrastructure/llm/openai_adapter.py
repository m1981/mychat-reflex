from typing import AsyncGenerator, List, Optional, Dict, Any
from openai import AsyncOpenAI
from src.core.domain.interfaces import ILLMService
from src.core.domain.entities import (
    ChatMessage,
    LLMConfig,
    Role,
    TextPart,
    ImagePart,
    DocumentPart,
)


class OpenAIAdapter(ILLMService):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_stream(
        self, messages: List[ChatMessage], config: Optional[LLMConfig] = None
    ) -> AsyncGenerator[str, None]:
        config = config or LLMConfig()
        openai_messages = []

        # --- ADR 010: System Prompt Resolution Strategy ---
        # OpenAI o1/o3 models require 'developer' instead of 'system'
        is_reasoning_model = self.model.startswith(("o1", "o3"))
        system_role_target = "developer" if is_reasoning_model else "system"

        for msg in messages:
            # Resolve the role
            role = system_role_target if msg.role == Role.SYSTEM else msg.role.value

            # --- ADR 009: Polymorphic Message Content ---
            if isinstance(msg.content, str):
                # Legacy/Standard string content
                formatted_content = msg.content
            else:
                # Multimodal array content
                formatted_content = []
                for part in msg.content:
                    if isinstance(part, TextPart):
                        formatted_content.append({"type": "text", "text": part.text})
                    elif isinstance(part, ImagePart):
                        formatted_content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{part.mime_type};base64,{part.base64_data}"
                                },
                            }
                        )
                    elif isinstance(part, DocumentPart):
                        # Note: Standard OpenAI Chat API doesn't accept base64 PDFs directly
                        # like Anthropic does. We handle the edge case gracefully here.
                        formatted_content.append(
                            {
                                "type": "text",
                                "text": f"[Document attached: {part.mime_type}]",
                            }
                        )

            openai_messages.append({"role": role, "content": formatted_content})

        # --- ADR 008: Normalization of Advanced Reasoning ---
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "stream": True,
        }

        if config.enable_reasoning and is_reasoning_model:
            # 1. Map integer budget to OpenAI's string enum heuristic
            if config.reasoning_budget:
                if config.reasoning_budget < 2000:
                    kwargs["reasoning_effort"] = "low"
                elif config.reasoning_budget < 8000:
                    kwargs["reasoning_effort"] = "medium"
                else:
                    kwargs["reasoning_effort"] = "high"
            else:
                kwargs["reasoning_effort"] = "medium"

            # 2. CRITICAL: OpenAI o1/o3 models reject the temperature parameter.
            # We intentionally do NOT pass temperature here to prevent 400 Bad Request.
        else:
            # Standard models (gpt-4o) get the temperature
            kwargs["temperature"] = config.temperature

        # Call the API and stream the response
        stream = await self.client.chat.completions.create(**kwargs)

        # Yield raw text chunks back to the Use Case
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
