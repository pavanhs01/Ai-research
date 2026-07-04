from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthenticatedUser
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def get_or_create_from_clerk(self, auth_user: AuthenticatedUser) -> User:
        """
        Idempotent sync: called on every authenticated request via the
        `get_current_db_user` dependency. If the Clerk session is the
        user's first request, a local User row is created on the fly so
        the rest of the app never has to special-case "unsynced" users.
        Primary sync still happens via the Clerk webhook (see
        api/v1/endpoints/auth.py) — this is a safety-net fallback.
        """
        existing = await self.repo.get_by_clerk_id(auth_user.clerk_id)
        if existing:
            return existing

        if not auth_user.email:
            raise ValueError("Cannot create user without an email claim from Clerk")

        logger.info("Creating local user record for clerk_id=%s", auth_user.clerk_id)
        return await self.repo.create(
            UserCreate(clerk_id=auth_user.clerk_id, email=auth_user.email, full_name=None, avatar_url=None)
        )

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        return await self.repo.update(user, data)

    async def list_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        return await self.repo.list_all(limit=limit, offset=offset)

    async def deactivate(self, user: User) -> User:
        return await self.repo.deactivate(user)
