from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_admin
from app.db.session import get_db
from app.models.document import Document
from app.models.project import Project
from app.models.subscription import PlanTier, Subscription
from app.models.user import User
from app.schemas.user import UserRead
from app.services.user_service import UserService

router = APIRouter(tags=["admin"])


@router.get("/users", response_model=list[UserRead])
async def list_users(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    return await UserService(db).list_users(limit=limit, offset=offset)


@router.get("/stats")
async def platform_stats(_: User = Depends(require_admin), db: AsyncSession = Depends(get_db)) -> dict:
    total_users = await db.scalar(select(func.count()).select_from(User))
    total_projects = await db.scalar(select(func.count()).select_from(Project))
    total_documents = await db.scalar(select(func.count()).select_from(Document))
    paying_subscribers = await db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.plan != PlanTier.FREE)
    )

    return {
        "total_users": total_users or 0,
        "total_projects": total_projects or 0,
        "total_documents": total_documents or 0,
        "paying_subscribers": paying_subscribers or 0,
    }
