import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_db_user
from app.core.exceptions import ForbiddenException, NotFoundException
from app.db.session import get_db
from app.models.conversation import MessageRole
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.chat import ChatRequest, ChatResponse, ConversationRead, ConversationRename, ConversationWithMessages
from app.services.project_service import ProjectService
from app.services.rag_service import rag_service

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    await ProjectService(db).get_owned(payload.project_id, user.id)
    conv_repo = ConversationRepository(db)

    # Existing conversation: load with messages for history context
    history: list[dict] = []
    if payload.conversation_id:
        conversation = await conv_repo.get_by_id(payload.conversation_id, with_messages=True)
        if conversation is None or conversation.owner_id != user.id:
            raise NotFoundException("Conversation not found.")
        # Build history from already-loaded messages (selectinload, no lazy access)
        loaded_messages = conversation.messages if conversation.messages is not None else []  # type: ignore[attr-defined]
        history = [
            {"role": m.role.value, "content": m.content} for m in loaded_messages
        ][-10:]
    else:
        # New conversation — no history yet
        title = payload.message[:60] + ("..." if len(payload.message) > 60 else "")
        conversation = await conv_repo.create(payload.project_id, user.id, title=title)

    await conv_repo.add_message(conversation.id, MessageRole.USER, payload.message)

    answer_text, citations = await rag_service.answer(db, payload.project_id, payload.message, history)

    assistant_message = await conv_repo.add_message(
        conversation.id,
        MessageRole.ASSISTANT,
        answer_text,
        citations=[c.model_dump(mode="json") for c in citations],
    )

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        answer=answer_text,
        citations=citations,
    )


@router.get("/conversations/{project_id}", response_model=list[ConversationRead])
async def list_conversations(
    project_id: uuid.UUID, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    await ProjectService(db).get_owned(project_id, user.id)
    return await ConversationRepository(db).list_for_project(project_id)


@router.get("/conversations/detail/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: uuid.UUID, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    conv_repo = ConversationRepository(db)
    conversation = await conv_repo.get_by_id(conversation_id, with_messages=True)
    if conversation is None:
        raise NotFoundException("Conversation not found.")
    if conversation.owner_id != user.id:
        raise ForbiddenException("You do not have access to this conversation.")
    return conversation


@router.patch("/conversations/{conversation_id}", response_model=ConversationRead)
async def rename_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationRename,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    conv_repo = ConversationRepository(db)
    conversation = await conv_repo.get_by_id(conversation_id)
    if conversation is None:
        raise NotFoundException("Conversation not found.")
    if conversation.owner_id != user.id:
        raise ForbiddenException("You do not have access to this conversation.")
    return await conv_repo.update_title(conversation, payload.title)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    conv_repo = ConversationRepository(db)
    conversation = await conv_repo.get_by_id(conversation_id)
    if conversation is None:
        raise NotFoundException("Conversation not found.")
    if conversation.owner_id != user.id:
        raise ForbiddenException("You do not have access to this conversation.")
    await conv_repo.delete(conversation)
