"""
LLM Service Interfaces and Adapters.

This module contains:
- ILLMService: Abstract interface for LLM providers
- LLMConfig: Configuration for LLM generation
- Role: Enum for message roles
- AnthropicAdapter: Concrete implementation for Anthropic Claude
- OpenAIAdapter: Concrete implementation for OpenAI GPT

This preserves Clean Architecture principles - use cases depend on
the ILLMService interface, not concrete implementations.

Migrated from src/core/domain/ (Phase 1, Task 1.2)
Simplified for Reflex monolith - string content only (no multimodal for MVP).
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncGenerator, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================================================
# DOMAIN ENTITIES
# ============================================================================


class Role(str, Enum):
    """Message role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class LLMConfig(BaseModel):
    """Configuration for LLM generation."""

    temperature: float = 0.7
    enable_reasoning: bool = False
    reasoning_budget: Optional[int] = None


# ============================================================================
# INTERFACES (PORTS)
# ============================================================================


class ILLMService(ABC):
    """
    Abstract interface for LLM service providers.

    Use cases depend on this interface, not concrete implementations.
    This enables swapping providers (Anthropic, OpenAI, local models) without
    changing business logic.
    """

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream text chunks from the LLM.

        Args:
            prompt: User input text
            config: Optional LLM configuration

        Yields:
            Text chunks as they arrive from the LLM
        """
        pass


# ============================================================================
# ADAPTERS (IMPLEMENTATIONS)
# ============================================================================


class AnthropicAdapter(ILLMService):
    """
    Anthropic Claude adapter.

    Simplified for Reflex monolith - string-only prompts.
    No multimodal content support in MVP.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4.5"):
        """
        Initialize Anthropic adapter.

        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-sonnet-4-5)
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
    No multimodal content support in MVP.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize OpenAI adapter.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4o)
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
            # Map reasoning budget to OpenAI's effort levels
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
