import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk


class ChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, chunks: list[Chunk]) -> list[Chunk]:
        self.db.add_all(chunks)
        await self.db.commit()
        for c in chunks:
            await self.db.refresh(c)
        return chunks

    async def get_by_ids(self, chunk_ids: list[uuid.UUID]) -> list[Chunk]:
        if not chunk_ids:
            return []
        result = await self.db.execute(select(Chunk).where(Chunk.id.in_(chunk_ids)))
        return list(result.scalars().all())

    async def list_for_document(self, document_id: uuid.UUID) -> list[Chunk]:
        result = await self.db.execute(
            select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
        )
        return list(result.scalars().all())

    async def mark_embedded(self, chunk_ids: list[uuid.UUID]) -> None:
        chunks = await self.get_by_ids(chunk_ids)
        for c in chunks:
            c.embedded = True
        await self.db.commit()
