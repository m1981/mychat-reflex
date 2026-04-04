import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Assume get_send_message_use_case is defined in your DI container setup
from src.core.di import get_send_message_use_case
from src.features.chat.use_cases.send_message import SendMessageUseCase

router = APIRouter(prefix="/chat", tags=["Chat"])


# API Contract
class SendMessageRequest(BaseModel):
    content: str


@router.post("/{conversation_id}/stream")
async def stream_chat_message(
        conversation_id: str,
        request: SendMessageRequest,
        use_case: SendMessageUseCase = Depends(get_send_message_use_case)
):
    """
    Streams a ChatGPT-like response using Server-Sent Events (SSE).
    """

    async def event_publisher():
        # Iterate over the dictionaries yielded by the Use Case
        async for event_dict in use_case.execute(conversation_id, request.content):
            # Extract the event type and data payload
            event_type = event_dict.get("event", "message")
            data_payload = json.dumps(event_dict.get("data", {}))

            # Format strictly according to the SSE specification
            # Format:
            # event: event_name\n
            # data: {"json": "payload"}\n\n
            yield f"event: {event_type}\ndata: {data_payload}\n\n"

    return StreamingResponse(
        event_publisher(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disables buffering in Nginx if deployed
        }
    )