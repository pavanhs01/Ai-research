"""Integration tests for billing endpoints (Stripe mocked)."""
import pytest
from unittest.mock import patch, MagicMock
from app.api.v1.deps import get_current_db_user
from app.main import app


def make_auth_override(user):
    async def _override():
        return user
    return _override


@pytest.mark.asyncio
async def test_get_subscription_defaults_to_free(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        response = await client.get("/api/v1/billing/subscription")
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "free"
        assert data["status"] == "active"
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_checkout_session_created(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/pay/test_session_123"
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"

        with patch("stripe.Customer.create", return_value=mock_customer), \
             patch("stripe.checkout.Session.create", return_value=mock_session), \
             patch("app.services.billing_service.settings") as mock_settings:
            mock_settings.STRIPE_SECRET_KEY = "sk_test_fake"
            mock_settings.FRONTEND_ORIGIN = "http://localhost:3000"

            response = await client.post("/api/v1/billing/checkout", json={"plan": "pro"})

        assert response.status_code == 200
        assert "checkout_url" in response.json()
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_checkout_fails_clearly_when_price_id_unconfigured(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"

        with patch("stripe.Customer.create", return_value=mock_customer), \
             patch("app.services.billing_service.settings") as mock_settings:
            mock_settings.STRIPE_SECRET_KEY = "sk_test_fake"
            mock_settings.STRIPE_PRICE_ID_PRO = ""
            mock_settings.FRONTEND_ORIGIN = "http://localhost:3000"

            response = await client.post("/api/v1/billing/checkout", json={"plan": "pro"})

        assert response.status_code == 502
        assert "Price ID" in response.json()["error"]["message"]
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_checkout_for_free_plan_rejected(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        with patch("app.services.billing_service.settings") as mock_settings:
            mock_settings.STRIPE_SECRET_KEY = "sk_test_fake"
            response = await client.post("/api/v1/billing/checkout", json={"plan": "free"})
        assert response.status_code == 400
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)
