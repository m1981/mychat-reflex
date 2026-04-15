"""
Infrastructure Layer: LLM Adapters.

This module contains the concrete implementations of the ILLMService interface.
By keeping this in the infrastructure layer, we protect the core domain and
use cases from third-party SDK changes (OpenAI, Anthropic).

Architectural Rule:
- Lazy imports are used for third-party SDKs so the app doesn't crash
  if a specific provider's package isn't installed.
"""

import logging
from typing import AsyncGenerator, Optional

from mychat_reflex.core.llm_ports import ILLMService, LLMConfig

logger = logging.getLogger(__name__)


class AnthropicAdapter(ILLMService):
    """
    Anthropic Claude adapter.
    Simplified for Reflex monolith - string-only prompts.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4.5"):
        """
        Initialize Anthropic adapter.
        """
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        logger.info(f"[AnthropicAdapter] Initialized with model: {self.model}")

    async def generate_stream(
        self,
        prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response from Anthropic Claude."""
        config = config or LLMConfig()

        logger.info("=" * 80)
        logger.info("[AnthropicAdapter] 🚀 STARTING NEW API REQUEST")
        logger.info("=" * 80)
        logger.info(f"[AnthropicAdapter] Model: {self.model}")
        logger.info(f"[AnthropicAdapter] Temperature: {config.temperature}")
        logger.info(f"[AnthropicAdapter] Reasoning enabled: {config.enable_reasoning}")
        logger.info(f"[AnthropicAdapter] Prompt length: {len(prompt)} characters")
        logger.info("-" * 80)
        logger.info("[AnthropicAdapter] FULL PROMPT:")
        logger.info("-" * 80)
        logger.info(prompt)
        logger.info("-" * 80)

        # Build API request
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": config.temperature,
        }

        # Add extended thinking if enabled
        if config.enable_reasoning and "claude-sonnet-4" in self.model:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": config.reasoning_budget or 2000,
            }
            logger.info("[AnthropicAdapter] ✅ Extended thinking enabled")
            logger.info(
                f"[AnthropicAdapter] Thinking budget: {kwargs['thinking']['budget_tokens']} tokens"
            )

        # Log the complete API request payload
        logger.info("=" * 80)
        logger.info("[AnthropicAdapter] 📤 ANTHROPIC API REQUEST PAYLOAD:")
        logger.info("=" * 80)
        import json

        logger.info(json.dumps(kwargs, indent=2, default=str))
        logger.info("=" * 80)

        try:
            chunk_count = 0
            total_chars = 0
            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    chunk_count += 1
                    total_chars += len(text)
                    if chunk_count == 1:
                        logger.info("[AnthropicAdapter] ✅ First chunk received!")
                        logger.info(
                            f"[AnthropicAdapter] First chunk content: {repr(text[:100])}"
                        )
                    if chunk_count % 10 == 0:
                        logger.debug(
                            f"[AnthropicAdapter] Chunk #{chunk_count}, total chars: {total_chars}"
                        )
                    yield text

            logger.info("=" * 80)
            logger.info("[AnthropicAdapter] ✅ STREAM COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            logger.info(f"[AnthropicAdapter] Total chunks received: {chunk_count}")
            logger.info(f"[AnthropicAdapter] Total characters: {total_chars}")
            logger.info("=" * 80)

        except Exception as e:
            logger.error("=" * 80)
            logger.error("[AnthropicAdapter] ❌ ERROR OCCURRED")
            logger.error("=" * 80)
            logger.error(f"[AnthropicAdapter] Error type: {type(e).__name__}")
            logger.error(f"[AnthropicAdapter] Error message: {str(e)}")
            logger.error("=" * 80)
            raise


class OpenAIAdapter(ILLMService):
    """
    OpenAI GPT adapter.
    Simplified for Reflex monolith - string-only prompts.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize OpenAI adapter.
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        logger.info(f"[OpenAIAdapter] Initialized with model: {self.model}")

    async def generate_stream(
        self,
        prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI GPT."""
        config = config or LLMConfig()

        logger.info(f"[OpenAIAdapter] Generating response for prompt: {prompt[:50]}...")
        logger.debug(f"[OpenAIAdapter] Config: temp={config.temperature}")

        # Build messages array
        messages = [{"role": "user", "content": prompt}]

        # Handle o1/o3 reasoning models differently
        is_reasoning_model = self.model.startswith(("o1", "o3"))

        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        # Add temperature (not supported by o1/o3 models)
        if not is_reasoning_model:
            kwargs["temperature"] = config.temperature

        # Add reasoning effort for o1/o3 models
        if config.enable_reasoning and is_reasoning_model:
            if config.reasoning_budget:
                if config.reasoning_budget < 2000:
                    kwargs["reasoning_effort"] = "low"
                elif config.reasoning_budget < 8000:
                    kwargs["reasoning_effort"] = "medium"
                else:
                    kwargs["reasoning_effort"] = "high"
            else:
                kwargs["reasoning_effort"] = "medium"
            logger.debug(
                f"[OpenAIAdapter] Reasoning effort: {kwargs['reasoning_effort']}"
            )

        try:
            chunk_count = 0
            response = await self.client.chat.completions.create(**kwargs)

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_count += 1
                    if chunk_count == 1:
                        logger.info("[OpenAIAdapter] First chunk received")
                    yield chunk.choices[0].delta.content

            logger.info(f"[OpenAIAdapter] Stream completed. Chunks: {chunk_count}")

        except Exception as e:
            logger.error(f"[OpenAIAdapter] Error: {type(e).__name__}: {str(e)}")
            raise
