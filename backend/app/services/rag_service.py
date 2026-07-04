import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.chunk_repository import ChunkRepository
from app.schemas.chat import Citation
from app.services.embedding_service import embedding_service
from app.services.openai_service import openai_service
from app.services.vector_store_service import project_namespace, vector_store

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an advanced AI Research Assistant. Answer ONLY using the retrieved context. Never hallucinate. If the answer is unavailable, respond: "I could not find this in the uploaded documents." Always cite the filename, page number, and section. If documents conflict, explain the conflict. Format responses in Markdown."""

DEFAULT_TOP_K = 8


class RAGService:
    async def retrieve(self, db: AsyncSession, project_id: uuid.UUID, query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
        query_vector = await embedding_service.embed_query(query)
        namespace = project_namespace(project_id)
        matches = await vector_store.query(vector=query_vector, top_k=top_k, namespace=namespace)

        chunk_repo = ChunkRepository(db)
        chunk_ids = [uuid.UUID(m["id"]) for m in matches]
        chunks_by_id = {str(c.id): c for c in await chunk_repo.get_by_ids(chunk_ids)}

        enriched = []
        for match in matches:
            chunk = chunks_by_id.get(match["id"])
            if chunk:
                enriched.append({"chunk": chunk, "score": match["score"]})
        return enriched

    def build_context(self, retrieved: list[dict]) -> str:
        blocks = []
        for item in retrieved:
            chunk = item["chunk"]
            location = f"{chunk.filename}"
            if chunk.page_number:
                location += f", page {chunk.page_number}"
            if chunk.section:
                location += f", section \"{chunk.section}\""
            blocks.append(f"[Source: {location}]\n{chunk.content}")
        return "\n\n---\n\n".join(blocks)

    async def answer(
        self, db: AsyncSession, project_id: uuid.UUID, query: str, conversation_history: list[dict] | None = None
    ) -> tuple[str, list[Citation]]:
        retrieved = await self.retrieve(db, project_id, query)

        if not retrieved:
            return "I could not find this in the uploaded documents.", []

        context = self.build_context(retrieved)
        user_prompt = (
            f"Context from the uploaded documents:\n\n{context}\n\n"
            f"---\n\nQuestion: {query}\n\n"
            "Answer using ONLY the context above. Cite filename, page number, and section for every claim."
        )

        messages = list(conversation_history or [])
        messages.append({"role": "user", "content": user_prompt})

        answer_text = await openai_service.chat_completion(system_prompt=SYSTEM_PROMPT, messages=messages)

        citations = [
            Citation(
                chunk_id=item["chunk"].id,
                filename=item["chunk"].filename,
                page_number=item["chunk"].page_number,
                section=item["chunk"].section,
                snippet=item["chunk"].content[:280],
            )
            for item in retrieved
        ]
        return answer_text, citations


rag_service = RAGService()
