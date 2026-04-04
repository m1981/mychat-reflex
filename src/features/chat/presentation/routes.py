import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Assume get_send_message_use_case is defined in your DI container setup
from src.core.di import get_send_message_use_case
from src.features.chat.use_cases.send_message import SendMessageUseCase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# API Contract
class SendMessageRequest(BaseModel):
    content: str


@router.post("/{conversation_id}/stream")
async def stream_chat_message(
    conversation_id: str,
    request: SendMessageRequest,
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
):
    """
    Streams a ChatGPT-like response using Server-Sent Events (SSE).
    """
    logger.info(
        f"[Routes] POST /chat/{conversation_id}/stream - Message: {request.content[:50]}..."
    )

    async def event_publisher():
        event_count = 0
        try:
            # Iterate over the dictionaries yielded by the Use Case
            async for event_dict in use_case.execute(conversation_id, request.content):
                event_count += 1
                # Extract the event type and data payload
                event_type = event_dict.get("event", "message")
                data_payload = json.dumps(event_dict.get("data", {}))

                if event_count == 1:
                    logger.debug(f"[Routes] First event: {event_type}")

                # Format strictly according to the SSE specification
                # Format:
                # event: event_name\n
                # data: {"json": "payload"}\n\n
                yield f"event: {event_type}\ndata: {data_payload}\n\n"

            logger.info(f"[Routes] Stream completed. Total events: {event_count}")

        except Exception as e:
            logger.error(
                f"[Routes] Error in event_publisher: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            # Send error event to client
            error_payload = json.dumps({"message": f"Server error: {str(e)}"})
            yield f"event: error\ndata: {error_payload}\n\n"

    return StreamingResponse(
        event_publisher(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disables buffering in Nginx if deployed
        },
    )
