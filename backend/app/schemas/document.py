import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.document import DocumentSourceType, DocumentStatus


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: DocumentStatus


class DocumentUrlIngestRequest(BaseModel):
    project_id: uuid.UUID
    url: HttpUrl


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    source_type: DocumentSourceType
    source_url: str | None
    mime_type: str | None
    file_size_bytes: int | None
    status: DocumentStatus
    error_message: str | None
    page_count: int | None
    summary: str | None
    created_at: datetime
    updated_at: datetime


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    chunk_index: int
    page_number: int | None
    section: str | None
    filename: str


class DocumentSummaryRequest(BaseModel):
    document_id: uuid.UUID
