from pydantic import BaseModel

from app.models.subscription import PlanTier, SubscriptionStatus


class CheckoutSessionRequest(BaseModel):
    plan: PlanTier


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class SubscriptionRead(BaseModel):
    plan: PlanTier
    status: SubscriptionStatus
    current_period_end: str | None


class BillingPortalResponse(BaseModel):
    portal_url: str
