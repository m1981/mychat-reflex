#!/usr/bin/env python3
"""
Integration test to verify Anthropic is wired correctly through the entire system.
Tests: AnthropicAdapter -> SendMessageUseCase
Run this after setting ANTHROPIC_API_KEY environment variable.
"""

import asyncio
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

from mychat_reflex.core.llm_ports import AnthropicAdapter, LLMConfig
from mychat_reflex.features.chat.use_cases import SendMessageUseCase
from mychat_reflex.features.chat.models import Message

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


@pytest.mark.integration
async def test_anthropic_adapter_direct():
    """Test 1: Direct adapter test"""
    print("\n" + "=" * 60)
    print("TEST 1: Direct Anthropic Adapter")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        pytest.skip("ANTHROPIC_API_KEY not set in .env file")

    adapter = AnthropicAdapter(api_key=api_key, model="claude-sonnet-4-5")

    # ARCHITECT FIX: The adapter now takes a string, not a list of objects
    prompt = "Say 'Hello from Anthropic!' in one sentence."

    print("📡 Streaming response from Claude...\n")
    full_response = ""
    async for chunk in adapter.generate_stream(prompt, LLMConfig(temperature=0.7)):
        print(chunk, end="", flush=True)
        full_response += chunk

    print("\n\n✅ Direct adapter test passed!")
    assert len(full_response) > 0, "Response should not be empty"


@pytest.mark.integration
async def test_use_case_integration():
    """Test 2: Full use case integration"""
    print("\n" + "=" * 60)
    print("TEST 2: Full Use Case Integration")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        pytest.skip("ANTHROPIC_API_KEY not set in .env file")

    llm_service = AnthropicAdapter(api_key=api_key, model="claude-sonnet-4-5")
    use_case = SendMessageUseCase(llm_service=llm_service)

    conversation_id = "test-conversation-001"
    user_message = "What is ESP32? Reply in one short sentence."

    # Create fake history
    history = [
        Message(id="1", conversation_id=conversation_id, role="user", content="Hi"),
        Message(
            id="2", conversation_id=conversation_id, role="assistant", content="Hello!"
        ),
    ]

    print("📡 Executing use case with test message...\n")
    full_response = ""
    chunk_count = 0

    # ARCHITECT FIX: Yields raw strings now, not SSE dictionaries
    async for chunk in use_case.execute(conversation_id, user_message, history=history):
        chunk_count += 1
        print(chunk, end="", flush=True)
        full_response += chunk

    print("\n\n✅ Use case integration test passed!")
    assert chunk_count > 0, "Should receive at least one chunk"
    assert len(full_response) > 0, "Should receive response from LLM"


if __name__ == "__main__":
    asyncio.run(test_anthropic_adapter_direct())
    asyncio.run(test_use_case_integration())
