import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentSourceType, DocumentStatus


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        project_id: uuid.UUID,
        owner_id: uuid.UUID,
        filename: str,
        source_type: DocumentSourceType,
        source_url: str | None = None,
        storage_key: str | None = None,
        mime_type: str | None = None,
        file_size_bytes: int | None = None,
    ) -> Document:
        doc = Document(
            project_id=project_id,
            owner_id=owner_id,
            filename=filename,
            source_type=source_type,
            source_url=source_url,
            storage_key=storage_key,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            status=DocumentStatus.PENDING,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def list_for_project(self, project_id: uuid.UUID) -> list[Document]:
        result = await self.db.execute(
            select(Document).where(Document.project_id == project_id).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self, document: Document, status: DocumentStatus, error_message: str | None = None
    ) -> Document:
        document.status = status
        document.error_message = error_message
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def set_page_count(self, document: Document, page_count: int) -> Document:
        document.page_count = page_count
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def set_summary(self, document: Document, summary: str) -> Document:
        document.summary = summary
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete(self, document: Document) -> None:
        await self.db.delete(document)
        await self.db.commit()
