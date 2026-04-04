from typing import AsyncGenerator, Dict, Any
from src.core.domain.interfaces import IConversationRepo, IVectorStore, ILLMService
from src.core.domain.entities import Role
from src.features.chat.domain.services.prompt_builder import RAGPromptBuilder


class SendMessageUseCase:
    def __init__(
            self,
            conversation_repo: IConversationRepo,
            vector_store: IVectorStore,
            llm_service: ILLMService,
            prompt_builder: RAGPromptBuilder
    ):
        self.repo = conversation_repo
        self.vector_store = vector_store
        self.llm = llm_service
        self.prompt_builder = prompt_builder

    async def execute(self, conversation_id: str, content: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes the RAG chat flow and yields structured events for SSE streaming.
        """
        try:
            # 1. Persist User Message immediately
            await self.repo.save_message(conversation_id, Role.USER, content)

            # 2. Retrieve Context (RAG)
            # Yield an event so the UI can show "Searching knowledge base..."
            yield {"event": "status", "data": {"message": "Searching knowledge base..."}}

            search_results = await self.vector_store.search(query=content, limit=5)

            # Yield the sources so the UI can render citations/links
            yield {
                "event": "sources_found",
                "data": [result.model_dump() for result in search_results]
            }

            # 3. Prepare the Prompt
            history = await self.repo.get_history(conversation_id)
            messages_for_llm = self.prompt_builder.build_messages(history, search_results)

            # 4. Stream the LLM Response
            full_response_text = ""

            async for chunk in self.llm.generate_stream(messages_for_llm):
                full_response_text += chunk
                # Yield each text delta to the frontend
                yield {
                    "event": "content_chunk",
                    "data": {"text": chunk}
                }

            # 5. Persist the Assistant's final message
            await self.repo.save_message(conversation_id, Role.ASSISTANT, full_response_text)

            # 6. Signal Completion
            yield {
                "event": "message_complete",
                "data": {"full_text": full_response_text}
            }

        except Exception as e:
            # Catch errors and stream them to the UI gracefully
            yield {
                "event": "error",
                "data": {"message": f"An error occurred: {str(e)}"}
            }