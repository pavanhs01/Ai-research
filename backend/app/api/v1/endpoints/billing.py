from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_db_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.billing import (
    BillingPortalResponse,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    SubscriptionRead,
)
from app.services.billing_service import billing_service

router = APIRouter()


@router.get("/subscription", response_model=SubscriptionRead)
async def get_subscription(user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)):
    subscription = await SubscriptionRepository(db).get_or_create(user.id)
    return subscription


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout(
    payload: CheckoutSessionRequest, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    url = await billing_service.create_checkout_session(db, user, payload.plan)
    return CheckoutSessionResponse(checkout_url=url)


@router.post("/portal", response_model=BillingPortalResponse)
async def create_portal(user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)):
    url = await billing_service.create_portal_session(db, user)
    return BillingPortalResponse(portal_url=url)


@router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request, db: AsyncSession = Depends(get_db), stripe_signature: str = Header(None, alias="stripe-signature")
):
    payload = await request.body()
    event = billing_service.verify_webhook(payload, stripe_signature)
    await billing_service.handle_webhook_event(db, event)
    return {"received": True}
