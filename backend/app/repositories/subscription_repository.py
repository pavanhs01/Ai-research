import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import PlanTier, Subscription, SubscriptionStatus


class SubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: uuid.UUID) -> Subscription | None:
        result = await self.db.execute(select(Subscription).where(Subscription.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_by_stripe_customer_id(self, customer_id: str) -> Subscription | None:
        result = await self.db.execute(select(Subscription).where(Subscription.stripe_customer_id == customer_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: uuid.UUID) -> Subscription:
        existing = await self.get_by_user_id(user_id)
        if existing:
            return existing
        sub = Subscription(user_id=user_id, plan=PlanTier.FREE, status=SubscriptionStatus.ACTIVE)
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def update_from_stripe(
        self,
        subscription: Subscription,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
        plan: PlanTier | None = None,
        status: SubscriptionStatus | None = None,
        current_period_end: str | None = None,
    ) -> Subscription:
        if stripe_customer_id is not None:
            subscription.stripe_customer_id = stripe_customer_id
        if stripe_subscription_id is not None:
            subscription.stripe_subscription_id = stripe_subscription_id
        if plan is not None:
            subscription.plan = plan
        if status is not None:
            subscription.status = status
        if current_period_end is not None:
            subscription.current_period_end = current_period_end
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription
