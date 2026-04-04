# File: src/infrastructure/vector_store/mock_adapter.py
import asyncio
from typing import List
from src.core.domain.interfaces import IVectorStore
from src.core.domain.entities import SearchResult


class MockVectorStore(IVectorStore):
    async def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        await asyncio.sleep(1)  # Simulate network delay
        return [
            SearchResult(
                id="1",
                text="ESP32 is a low-cost microcontroller with Wi-Fi.",
                score=0.9,
            ),
            SearchResult(id="2", text="It is widely used in IoT projects.", score=0.85),
        ]
