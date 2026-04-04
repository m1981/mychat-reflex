import logging
from typing import AsyncGenerator, Dict, Any
from src.core.domain.interfaces import IConversationRepo, IVectorStore, ILLMService
from src.core.domain.entities import Role, LLMConfig
from src.features.chat.domain.services.prompt_builder import RAGPromptBuilder

logger = logging.getLogger(__name__)


class SendMessageUseCase:
    def __init__(
        self,
        conversation_repo: IConversationRepo,
        vector_store: IVectorStore,
        llm_service: ILLMService,
        prompt_builder: RAGPromptBuilder,
    ):
        self.repo = conversation_repo
        self.vector_store = vector_store
        self.llm = llm_service
        self.prompt_builder = prompt_builder

    async def execute(
        self, conversation_id: str, content: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes the RAG chat flow and yields structured events for SSE streaming.
        """
        logger.info(
            f"[SendMessageUseCase] Starting execution for conversation: {conversation_id}"
        )
        logger.debug(f"[SendMessageUseCase] User message: {content[:100]}...")

        try:
            # 1. Persist User Message immediately
            logger.debug("[SendMessageUseCase] Saving user message to database")
            await self.repo.save_message(conversation_id, Role.USER, content)

            # 2. Retrieve Context (RAG)
            # Yield an event so the UI can show "Searching knowledge base..."
            logger.debug("[SendMessageUseCase] Searching vector store")
            yield {
                "event": "status",
                "data": {"message": "Searching knowledge base..."},
            }

            search_results = await self.vector_store.search(query=content, limit=5)
            logger.info(
                f"[SendMessageUseCase] Found {len(search_results)} search results"
            )

            # Yield the sources so the UI can render citations/links
            yield {
                "event": "sources_found",
                "data": [result.model_dump() for result in search_results],
            }

            # 3. Prepare the Prompt
            logger.debug("[SendMessageUseCase] Loading conversation history")
            history = await self.repo.get_history(conversation_id)
            logger.info(
                f"[SendMessageUseCase] Building prompt with {len(history)} history messages"
            )
            messages_for_llm = self.prompt_builder.build_messages(
                history, search_results
            )
            logger.debug(
                f"[SendMessageUseCase] Final prompt has {len(messages_for_llm)} messages"
            )

            # 4. Stream the LLM Response
            logger.info("[SendMessageUseCase] Starting LLM stream")
            full_response_text = ""
            chunk_count = 0

            llm_config = LLMConfig(temperature=0.7)
            async for chunk in self.llm.generate_stream(messages_for_llm, llm_config):
                chunk_count += 1
                full_response_text += chunk
                # Yield each text delta to the frontend
                yield {"event": "content_chunk", "data": {"text": chunk}}

            logger.info(
                f"[SendMessageUseCase] LLM stream completed. Chunks: {chunk_count}, Total chars: {len(full_response_text)}"
            )

            # 5. Persist the Assistant's final message
            logger.debug("[SendMessageUseCase] Saving assistant response to database")
            await self.repo.save_message(
                conversation_id, Role.ASSISTANT, full_response_text
            )

            # 6. Signal Completion
            logger.info("[SendMessageUseCase] Execution completed successfully")
            yield {
                "event": "message_complete",
                "data": {"full_text": full_response_text},
            }

        except Exception as e:
            # Catch errors and stream them to the UI gracefully
            logger.error(
                f"[SendMessageUseCase] Error occurred: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            yield {
                "event": "error",
                "data": {"message": f"An error occurred: {str(e)}"},
            }
