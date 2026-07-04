import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message, MessageRole


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, project_id: uuid.UUID, owner_id: uuid.UUID, title: str = "New conversation") -> Conversation:
        conv = Conversation(project_id=project_id, owner_id=owner_id, title=title)
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def get_by_id(self, conversation_id: uuid.UUID, with_messages: bool = False) -> Conversation | None:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        if with_messages:
            stmt = stmt.options(selectinload(Conversation.messages))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_project(self, project_id: uuid.UUID) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation).where(Conversation.project_id == project_id).order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def add_message(
        self, conversation_id: uuid.UUID, role: MessageRole, content: str, citations: list[dict] | None = None
    ) -> Message:
        message = Message(conversation_id=conversation_id, role=role, content=content, citations=citations)
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def update_title(self, conversation: Conversation, title: str) -> Conversation:
        conversation.title = title
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def delete(self, conversation: Conversation) -> None:
        await self.db.delete(conversation)
        await self.db.commit()
