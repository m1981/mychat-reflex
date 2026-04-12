from typing import List
from src.core.domain.entities import ChatMessage, Role, SearchResult


class RAGPromptBuilder:
    """
    Domain service responsible for constructing the final prompt array
    sent to the LLM, injecting RAG context safely.
    """

    def build_messages(
        self, history: List[ChatMessage], context: List[SearchResult]
    ) -> List[ChatMessage]:
        # 1. Format the retrieved context
        context_text = "\n\n".join(
            f"[Source {i + 1}]: {result.text}" for i, result in enumerate(context)
        )

        system_instruction = (
            "You are a helpful AI assistant. Use the following retrieved context "
            "to answer the user's question. If the answer is not in the context, "
            "say you don't know based on your notes.\n\n"
            f"CONTEXT:\n{context_text}"
        )

        # 2. Create the System Message
        messages = [ChatMessage(role=Role.SYSTEM, content=system_instruction)]

        # 3. Append the conversation history (which includes the latest user message)
        messages.extend(history)

        return messages
