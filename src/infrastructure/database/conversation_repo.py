# File: src/infrastructure/database/conversation_repo.py
import json
import uuid
from typing import List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.domain.interfaces import IConversationRepo
from src.core.domain.entities import (
    ChatMessage,
    Role,
    TextPart,
    ImagePart,
    DocumentPart,
)
from src.core.database.models import Conversation, Message as DBMessage


class SQLAlchemyConversationRepo(IConversationRepo):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_message(
        self, conversation_id: str, role: Role, content: Union[str, list]
    ) -> str:
        # 1. Ensure conversation exists
        conv = await self.session.get(Conversation, conversation_id)
        if not conv:
            conv = Conversation(id=conversation_id, title="New Chat")
            self.session.add(conv)

        # 2. Handle ADR 009: Polymorphic Content Serialization
        if isinstance(content, list):
            # Convert Pydantic parts to JSON string for the DB Text column
            db_content = json.dumps([part.model_dump() for part in content])
        else:
            db_content = content

        # 3. Create ORM Model
        msg_id = str(uuid.uuid4())
        db_msg = DBMessage(
            id=msg_id, conversation_id=conversation_id, role=role, content=db_content
        )
        self.session.add(db_msg)
        await self.session.commit()

        return msg_id

    async def get_history(self, conversation_id: str) -> List[ChatMessage]:
        # 1. Query ORM Models
        stmt = (
            select(DBMessage)
            .where(DBMessage.conversation_id == conversation_id)
            .order_by(DBMessage.created_at)
        )
        result = await self.session.execute(stmt)
        db_messages = result.scalars().all()

        domain_messages = []

        # 2. ADR 005: Map ORM Models to Pure Domain Models
        for db_msg in db_messages:
            parsed_content = db_msg.content

            # Attempt to deserialize JSON back into Polymorphic parts
            if parsed_content.strip().startswith("["):
                try:
                    raw_list = json.loads(parsed_content)
                    parts = []
                    for item in raw_list:
                        if item.get("type") == "text":
                            parts.append(TextPart(**item))
                        elif item.get("type") == "image":
                            parts.append(ImagePart(**item))
                        elif item.get("type") == "document":
                            parts.append(DocumentPart(**item))
                    parsed_content = parts
                except json.JSONDecodeError:
                    pass  # It was just a normal string that happened to start with '['

            domain_messages.append(
                ChatMessage(role=db_msg.role, content=parsed_content)
            )

        return domain_messages
