import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.chunk import Chunk
from app.models.document import DocumentStatus
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.parsing_service import parsing_service
from app.services.storage_service import storage_service

logger = get_logger(__name__)


class IngestionService:
    """
    Orchestrates: Parse -> Clean -> Chunk -> Embed -> Index.
    Invoked as a background task right after upload so the HTTP response
    returns immediately with status=pending; the frontend polls document
    status until it flips to `indexed` or `failed`.
    """

    async def run(self, db: AsyncSession, document_id: uuid.UUID) -> None:
        doc_repo = DocumentRepository(db)
        chunk_repo = ChunkRepository(db)

        document = await doc_repo.get_by_id(document_id)
        if document is None:
            logger.error("Ingestion called for missing document_id=%s", document_id)
            return

        try:
            await doc_repo.update_status(document, DocumentStatus.PARSING)

            if document.source_type.value == "url":
                pages = parsing_service.parse(source_type="url", url=document.source_url)
            else:
                raw_bytes = storage_service.download_bytes(document.storage_key)
                pages = parsing_service.parse(source_type=document.source_type.value, content=raw_bytes)

            page_numbers = [p.page_number for p in pages if p.page_number]
            if page_numbers:
                await doc_repo.set_page_count(document, max(page_numbers))

            await doc_repo.update_status(document, DocumentStatus.CHUNKING)
            prepared_chunks = chunking_service.chunk_pages(pages)

            if not prepared_chunks:
                await doc_repo.update_status(document, DocumentStatus.FAILED, "No content could be extracted.")
                return

            chunk_rows = [
                Chunk(
                    document_id=document.id,
                    project_id=document.project_id,
                    owner_id=document.owner_id,
                    content=pc.content,
                    chunk_index=pc.chunk_index,
                    token_count=pc.token_count,
                    filename=document.filename,
                    page_number=pc.page_number,
                    section=pc.section,
                    source_type=document.source_type.value,
                )
                for pc in prepared_chunks
            ]
            saved_chunks = await chunk_repo.bulk_create(chunk_rows)

            await doc_repo.update_status(document, DocumentStatus.EMBEDDING)
            await embedding_service.embed_and_index_chunks(saved_chunks)
            await chunk_repo.mark_embedded([c.id for c in saved_chunks])

            await doc_repo.update_status(document, DocumentStatus.INDEXED)
            logger.info("Document %s indexed with %d chunks.", document.id, len(saved_chunks))

        except Exception as exc:
            logger.exception("Ingestion failed for document_id=%s", document_id)
            await doc_repo.update_status(document, DocumentStatus.FAILED, str(exc)[:1000])


ingestion_service = IngestionService()
