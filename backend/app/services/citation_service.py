import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository


class CitationService:
    """
    Turns a chat response's citation chunk_ids into frontend-renderable
    highlight targets: which document, which page, and the exact text
    span to highlight when the user clicks a citation pill in the chat UI.
    """

    async def resolve_highlights(self, db: AsyncSession, chunk_ids: list[uuid.UUID]) -> list[dict]:
        chunk_repo = ChunkRepository(db)
        chunks = await chunk_repo.get_by_ids(chunk_ids)

        return [
            {
                "chunk_id": str(c.id),
                "document_id": str(c.document_id),
                "filename": c.filename,
                "page_number": c.page_number,
                "section": c.section,
                "highlight_text": c.content,
            }
            for c in chunks
        ]


citation_service = CitationService()
