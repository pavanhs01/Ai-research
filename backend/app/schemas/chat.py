import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.conversation import MessageRole


class Citation(BaseModel):
    chunk_id: uuid.UUID
    filename: str
    page_number: int | None
    section: str | None
    snippet: str


class ChatRequest(BaseModel):
    project_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    message: str = Field(..., min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    citations: list[Citation]


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    content: str
    citations: list[dict] | None
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class ConversationWithMessages(ConversationRead):
    messages: list[MessageRead] = []


class SearchRequest(BaseModel):
    project_id: uuid.UUID
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(8, ge=1, le=50)


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    filename: str
    page_number: int | None
    section: str | None
    content: str
    score: float
