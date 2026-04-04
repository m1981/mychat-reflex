from typing import AsyncGenerator, List
from openai import AsyncOpenAI
from src.core.domain.interfaces import ILLMService
from src.core.domain.entities import ChatMessage

class OpenAIAdapter(ILLMService):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_stream(self, messages: List[ChatMessage]) -> AsyncGenerator[str, None]:
        # 1. Translate Domain Models to OpenAI format
        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        # 2. Call the API and stream the response
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            stream=True
        )

        # 3. Yield raw text chunks back to the Use Case
        async for chunk in stream:
            # OpenAI sometimes sends empty delta chunks, so we check if content exists
            content = chunk.choices[0].delta.content
            if content is not None:
                yield content