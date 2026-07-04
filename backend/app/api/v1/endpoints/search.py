from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_db_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import SearchRequest, SearchResult
from app.services.project_service import ProjectService
from app.services.rag_service import rag_service

router = APIRouter()


@router.post("", response_model=list[SearchResult])
async def semantic_search(
    payload: SearchRequest, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    await ProjectService(db).get_owned(payload.project_id, user.id)
    retrieved = await rag_service.retrieve(db, payload.project_id, payload.query, top_k=payload.top_k)

    return [
        SearchResult(
            chunk_id=item["chunk"].id,
            filename=item["chunk"].filename,
            page_number=item["chunk"].page_number,
            section=item["chunk"].section,
            content=item["chunk"].content,
            score=item["score"],
        )
        for item in retrieved
    ]
