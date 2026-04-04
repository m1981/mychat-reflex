#!/usr/bin/env python3
"""
Integration test to verify Anthropic is wired correctly through the entire system.
Tests: AnthropicAdapter -> SendMessageUseCase -> Full RAG flow
Run this after setting ANTHROPIC_API_KEY environment variable.
"""

import asyncio
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

from src.infrastructure.llm.anthropic_adapter import AnthropicAdapter
from src.infrastructure.vector_store.mock_adapter import MockVectorStore
from src.infrastructure.database.conversation_repo import SQLAlchemyConversationRepo
from src.features.chat.domain.services.prompt_builder import RAGPromptBuilder
from src.features.chat.use_cases.send_message import SendMessageUseCase
from src.core.domain.entities import ChatMessage, Role, LLMConfig
from src.core.database.session import AsyncSessionLocal, init_db


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

    print("✅ API Key found")
    print("🔧 Initializing Anthropic adapter...")

    adapter = AnthropicAdapter(api_key=api_key, model="claude-sonnet-4-5")

    messages = [
        ChatMessage(role=Role.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(
            role=Role.USER, content="Say 'Hello from Anthropic!' in one sentence."
        ),
    ]

    print("📡 Streaming response from Claude...\n")

    full_response = ""
    async for chunk in adapter.generate_stream(messages, LLMConfig(temperature=0.7)):
        print(chunk, end="", flush=True)
        full_response += chunk

    print("\n\n✅ Direct adapter test passed!")
    print(f"📊 Total characters received: {len(full_response)}")

    assert len(full_response) > 0, "Response should not be empty"
    assert "anthropic" in full_response.lower() or "hello" in full_response.lower()


@pytest.mark.integration
async def test_use_case_integration():
    """Test 2: Full use case integration with RAG flow"""
    print("\n" + "=" * 60)
    print("TEST 2: Full Use Case Integration (RAG Flow)")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        pytest.skip("ANTHROPIC_API_KEY not set in .env file")

    print("🔧 Initializing database...")
    await init_db()

    print("🔧 Wiring dependencies...")
    async with AsyncSessionLocal() as session:
        # Wire up all dependencies
        conversation_repo = SQLAlchemyConversationRepo(session)
        vector_store = MockVectorStore()
        llm_service = AnthropicAdapter(api_key=api_key, model="claude-sonnet-4-5")
        prompt_builder = RAGPromptBuilder()

        use_case = SendMessageUseCase(
            conversation_repo=conversation_repo,
            vector_store=vector_store,
            llm_service=llm_service,
            prompt_builder=prompt_builder,
        )

        print("✅ Dependencies wired")
        print("📡 Executing use case with test message...\n")

        conversation_id = "test-conversation-001"
        user_message = "What is ESP32?"

        event_count = 0
        full_response = ""
        sources_found = False
        message_complete = False

        async for event in use_case.execute(conversation_id, user_message):
            event_count += 1
            event_type = event.get("event")
            data = event.get("data", {})

            if event_type == "status":
                print(f"\n[STATUS] {data.get('message')}")
            elif event_type == "sources_found":
                sources_found = True
                print(f"\n[SOURCES] Found {len(data)} sources")
                for i, source in enumerate(data):
                    print(f"  - Source {i + 1}: {source.get('text', '')[:50]}...")
            elif event_type == "content_chunk":
                text = data.get("text", "")
                print(text, end="", flush=True)
                full_response += text
            elif event_type == "message_complete":
                message_complete = True
                print("\n\n[COMPLETE] Message saved to database")
            elif event_type == "error":
                print(f"\n\n[ERROR] {data.get('message')}")
                pytest.fail(f"Use case returned error: {data.get('message')}")

        print("\n\n✅ Use case integration test passed!")
        print(f"📊 Total events: {event_count}")
        print(f"📊 Response length: {len(full_response)} characters")

        # Assertions
        assert event_count > 0, "Should receive at least one event"
        assert sources_found, "Should find sources from vector store"
        assert len(full_response) > 0, "Should receive response from LLM"
        assert message_complete, "Should complete message processing"

        # Verify message was saved to database
        print("\n🔍 Verifying database persistence...")
        history = await conversation_repo.get_history(conversation_id)
        print(f"✅ Found {len(history)} messages in database")

        assert len(history) >= 2, (
            "Should have at least user message and assistant response"
        )

        for msg in history:
            role_name = msg.role.value.upper()
            content_preview = (
                msg.content[:50]
                if isinstance(msg.content, str)
                else str(msg.content)[:50]
            )
            print(f"  - {role_name}: {content_preview}...")


if __name__ == "__main__":
    """Allow running tests directly without pytest"""

    async def main():
        print("\n🚀 Starting Anthropic Integration Tests")
        print("=" * 60)

        # Test 1: Direct adapter
        try:
            await test_anthropic_adapter_direct()
            test1_passed = True
        except Exception as e:
            print(f"\n❌ Test 1 failed: {e}")
            test1_passed = False

        if not test1_passed:
            print("\n❌ Test 1 failed. Skipping Test 2.")
            return

        # Test 2: Full integration
        try:
            await test_use_case_integration()
            test2_passed = True
        except Exception as e:
            print(f"\n❌ Test 2 failed: {e}")
            test2_passed = False

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(
            f"Test 1 (Direct Adapter): {'✅ PASSED' if test1_passed else '❌ FAILED'}"
        )
        print(
            f"Test 2 (Use Case Integration): {'✅ PASSED' if test2_passed else '❌ FAILED'}"
        )
        print("=" * 60)

        if test1_passed and test2_passed:
            print("\n🎉 All tests passed! Anthropic integration is working correctly.")
        else:
            print("\n❌ Some tests failed. Check the output above.")

    asyncio.run(main())
