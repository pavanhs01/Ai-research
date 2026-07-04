import uuid

from app.models.chunk import Chunk
from app.services.openai_service import openai_service
from app.services.vector_store_service import project_namespace, vector_store


class EmbeddingService:
    async def embed_and_index_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return

        texts = [c.content for c in chunks]
        embeddings = await openai_service.create_embeddings(texts)

        ids = [str(c.id) for c in chunks]
        metadatas = [
            {
                "user_id": str(c.owner_id),
                "project_id": str(c.project_id),
                "document_id": str(c.document_id),
                "filename": c.filename,
                "page_number": c.page_number or 0,
                "section": c.section or "",
                "chunk_id": str(c.id),
                "source_type": c.source_type,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        namespace = project_namespace(chunks[0].project_id)
        await vector_store.upsert(ids=ids, vectors=embeddings, metadatas=metadatas, namespace=namespace)

    async def embed_query(self, query: str) -> list[float]:
        embeddings = await openai_service.create_embeddings([query])
        return embeddings[0]

    async def delete_document_vectors(self, chunk_ids: list[uuid.UUID], project_id: uuid.UUID) -> None:
        await vector_store.delete(ids=[str(c) for c in chunk_ids], namespace=project_namespace(project_id))


embedding_service = EmbeddingService()
