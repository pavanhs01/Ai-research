"""
- GET /me               -> returns the authenticated user's profile (auto-creates on first call)
- POST /webhooks/clerk  -> primary sync path: Clerk calls this on user.created / user.updated / user.deleted
"""

from fastapi import APIRouter, Depends, Header, Request, status
from svix.webhooks import Webhook, WebhookVerificationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_db_user
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(tags=["auth"])
settings = get_settings()
logger = get_logger(__name__)


@router.get("/me", response_model=UserRead)
async def get_my_profile(current_user: User = Depends(get_current_db_user)) -> User:
    return current_user


@router.post("/webhooks/clerk", status_code=status.HTTP_200_OK)
async def clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    svix_id: str = Header(None, alias="svix-id"),
    svix_timestamp: str = Header(None, alias="svix-timestamp"),
    svix_signature: str = Header(None, alias="svix-signature"),
) -> dict:
    payload = await request.body()

    if not settings.CLERK_WEBHOOK_SECRET:
        raise AppException("Webhook secret not configured", status_code=500, code="config_error")

    try:
        wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
        event = wh.verify(
            payload,
            {"svix-id": svix_id, "svix-timestamp": svix_timestamp, "svix-signature": svix_signature},
        )
    except WebhookVerificationError as exc:
        logger.warning("Clerk webhook signature verification failed: %s", exc)
        raise AppException("Invalid webhook signature", status_code=400, code="invalid_signature") from exc

    event_type = event.get("type")
    data = event.get("data", {})
    repo = UserRepository(db)

    if event_type == "user.created":
        email = (data.get("email_addresses") or [{}])[0].get("email_address")
        if email and not await repo.get_by_clerk_id(data["id"]):
            await repo.create(
                UserCreate(
                    clerk_id=data["id"],
                    email=email,
                    full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or None,
                    avatar_url=data.get("image_url"),
                )
            )
            logger.info("Synced new user from Clerk webhook: %s", email)

    elif event_type == "user.updated":
        user = await repo.get_by_clerk_id(data["id"])
        if user:
            await repo.update(
                user,
                UserUpdate(
                    full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or None,
                    avatar_url=data.get("image_url"),
                ),
            )

    elif event_type == "user.deleted":
        user = await repo.get_by_clerk_id(data["id"])
        if user:
            await repo.deactivate(user)

    return {"received": True}
