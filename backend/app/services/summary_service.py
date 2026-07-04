from app.models.document import Document
from app.repositories.chunk_repository import ChunkRepository
from app.services.openai_service import openai_service
from sqlalchemy.ext.asyncio import AsyncSession

SUMMARY_SYSTEM_PROMPT = (
    "You are an AI Research Assistant. Summarize the provided document excerpts in 3-5 concise "
    "paragraphs using Markdown. Base the summary ONLY on the provided text — do not add outside "
    "knowledge. If the excerpts are insufficient for a full summary, say so explicitly."
)


class SummaryService:
    async def summarize_document(self, db: AsyncSession, document: Document) -> str:
        chunk_repo = ChunkRepository(db)
        chunks = await chunk_repo.list_for_document(document.id)

        if not chunks:
            return "This document has not finished processing yet, so no summary is available."

        combined = "\n\n".join(c.content for c in chunks[:40])  # cap context for very large docs
        user_prompt = f"Document: {document.filename}\n\nExcerpts:\n\n{combined}\n\nWrite the summary now."

        return await openai_service.chat_completion(
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=800,
        )


summary_service = SummaryService()
