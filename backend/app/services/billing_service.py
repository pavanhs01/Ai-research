import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException, ExternalServiceException
from app.core.logging import get_logger
from app.models.subscription import PlanTier, SubscriptionStatus
from app.models.user import User
from app.repositories.subscription_repository import SubscriptionRepository

settings = get_settings()
logger = get_logger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

STRIPE_STATUS_MAP = {
    "active": SubscriptionStatus.ACTIVE,
    "trialing": SubscriptionStatus.TRIALING,
    "past_due": SubscriptionStatus.PAST_DUE,
    "canceled": SubscriptionStatus.CANCELED,
    "incomplete": SubscriptionStatus.INCOMPLETE,
}


class BillingService:
    def _ensure_configured(self) -> None:
        if not settings.STRIPE_SECRET_KEY:
            raise ExternalServiceException("Billing is not configured on this server.")

    def _price_id_for(self, plan: PlanTier) -> str:
        price_id = {
            PlanTier.PRO: settings.STRIPE_PRICE_ID_PRO,
            PlanTier.TEAM: settings.STRIPE_PRICE_ID_TEAM,
        }.get(plan, "")
        if not price_id:
            raise ExternalServiceException(
                "No Stripe Price ID configured for the '"
                + plan.value
                + "' plan. Set STRIPE_PRICE_ID_"
                + plan.value.upper()
                + " in the environment."
            )
        return price_id

    async def create_checkout_session(self, db: AsyncSession, user: User, plan: PlanTier) -> str:
        self._ensure_configured()
        if plan == PlanTier.FREE:
            raise AppException("Cannot create a checkout session for the free plan.")

        repo = SubscriptionRepository(db)
        subscription = await repo.get_or_create(user.id)

        if not subscription.stripe_customer_id:
            customer = stripe.Customer.create(email=user.email, metadata={"user_id": str(user.id)})
            subscription = await repo.update_from_stripe(subscription, stripe_customer_id=customer.id)

        session = stripe.checkout.Session.create(
            customer=subscription.stripe_customer_id,
            mode="subscription",
            line_items=[{"price": self._price_id_for(plan), "quantity": 1}],
            success_url=f"{settings.FRONTEND_ORIGIN}/settings/billing?checkout=success",
            cancel_url=f"{settings.FRONTEND_ORIGIN}/settings/billing?checkout=canceled",
            metadata={"user_id": str(user.id), "plan": plan.value},
        )
        return session.url

    async def create_portal_session(self, db: AsyncSession, user: User) -> str:
        self._ensure_configured()
        repo = SubscriptionRepository(db)
        subscription = await repo.get_or_create(user.id)
        if not subscription.stripe_customer_id:
            raise AppException("No billing account found for this user yet.")

        portal = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=f"{settings.FRONTEND_ORIGIN}/settings/billing",
        )
        return portal.url

    def verify_webhook(self, payload: bytes, signature: str) -> dict:
        try:
            return stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
        except (stripe.error.SignatureVerificationError, ValueError) as exc:
            logger.warning("Stripe webhook verification failed: %s", exc)
            raise AppException("Invalid Stripe webhook signature.", 400, "invalid_signature") from exc

    async def handle_webhook_event(self, db: AsyncSession, event: dict) -> None:
        repo = SubscriptionRepository(db)
        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            user_id = data.get("metadata", {}).get("user_id")
            plan = data.get("metadata", {}).get("plan")
            if user_id and plan:
                import uuid as uuid_lib

                subscription = await repo.get_or_create(uuid_lib.UUID(user_id))
                await repo.update_from_stripe(
                    subscription,
                    stripe_subscription_id=data.get("subscription"),
                    plan=PlanTier(plan),
                    status=SubscriptionStatus.ACTIVE,
                )

        elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
            customer_id = data.get("customer")
            subscription = await repo.get_by_stripe_customer_id(customer_id)
            if subscription:
                stripe_status = data.get("status", "active")
                await repo.update_from_stripe(
                    subscription,
                    status=STRIPE_STATUS_MAP.get(stripe_status, SubscriptionStatus.ACTIVE),
                    current_period_end=str(data.get("current_period_end", "")),
                )


billing_service = BillingService()
