import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_db_user
from app.core.exceptions import NotFoundException
from app.db.session import AsyncSessionLocal, get_db
from app.models.document import DocumentSourceType
from app.models.user import User
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    ChunkRead,
    DocumentRead,
    DocumentUploadResponse,
    DocumentUrlIngestRequest,
)
from app.services.ingestion_service import ingestion_service
from app.services.project_service import ProjectService
from app.services.storage_service import storage_service
from app.services.summary_service import summary_service
from app.utils.file_validation import validate_upload

router = APIRouter()


async def _run_ingestion_isolated(document_id: uuid.UUID) -> None:
    """Background tasks need their own DB session, independent of the request's session lifecycle."""
    async with AsyncSessionLocal() as session:
        await ingestion_service.run(session, document_id)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    project_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    await ProjectService(db).get_owned(project_id, user.id)  # authorization check

    content = await file.read()
    source_type_str = validate_upload(file.filename, file.content_type, len(content))

    storage_key = storage_service.build_key(user.id, project_id, file.filename)
    storage_service.upload_bytes(storage_key, content, file.content_type or "application/octet-stream")

    doc_repo = DocumentRepository(db)
    document = await doc_repo.create(
        project_id=project_id,
        owner_id=user.id,
        filename=file.filename,
        source_type=DocumentSourceType(source_type_str),
        storage_key=storage_key,
        mime_type=file.content_type,
        file_size_bytes=len(content),
    )

    background_tasks.add_task(_run_ingestion_isolated, document.id)
    return DocumentUploadResponse(id=document.id, filename=document.filename, status=document.status)


@router.post("/ingest-url", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_url(
    payload: DocumentUrlIngestRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    await ProjectService(db).get_owned(payload.project_id, user.id)

    doc_repo = DocumentRepository(db)
    document = await doc_repo.create(
        project_id=payload.project_id,
        owner_id=user.id,
        filename=str(payload.url),
        source_type=DocumentSourceType.URL,
        source_url=str(payload.url),
    )

    background_tasks.add_task(_run_ingestion_isolated, document.id)
    return DocumentUploadResponse(id=document.id, filename=document.filename, status=document.status)


@router.get("/project/{project_id}", response_model=list[DocumentRead])
async def list_documents(
    project_id: uuid.UUID, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    await ProjectService(db).get_owned(project_id, user.id)
    return await DocumentRepository(db).list_for_project(project_id)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    document = await DocumentRepository(db).get_by_id(document_id)
    if document is None or document.owner_id != user.id:
        raise NotFoundException("Document not found.")
    return document


@router.get("/{document_id}/chunks", response_model=list[ChunkRead])
async def get_document_chunks(
    document_id: uuid.UUID, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    document = await DocumentRepository(db).get_by_id(document_id)
    if document is None or document.owner_id != user.id:
        raise NotFoundException("Document not found.")
    return await ChunkRepository(db).list_for_document(document_id)


@router.post("/{document_id}/summary", response_model=DocumentRead)
async def generate_summary(
    document_id: uuid.UUID, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)
    if document is None or document.owner_id != user.id:
        raise NotFoundException("Document not found.")

    summary = await summary_service.summarize_document(db, document)
    return await doc_repo.set_summary(document, summary)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)
    if document is None or document.owner_id != user.id:
        raise NotFoundException("Document not found.")

    if document.storage_key:
        storage_service.delete(document.storage_key)
    await doc_repo.delete(document)
