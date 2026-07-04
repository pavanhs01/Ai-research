from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import AuthenticatedUser, get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.user_service import UserService


async def get_current_db_user(
    auth_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolves the verified Clerk identity to a local Postgres User row, syncing on first sight."""
    try:
        return await UserService(db).get_or_create_from_clerk(auth_user)
    except ValueError as exc:
        raise UnauthorizedException(str(exc)) from exc


async def require_admin(user: User = Depends(get_current_db_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenException("Admin privileges required")
    return user
