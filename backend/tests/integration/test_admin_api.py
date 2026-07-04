"""Integration tests for admin endpoints."""
import pytest
from app.api.v1.deps import get_current_db_user, require_admin
from app.main import app


def make_auth_override(user):
    async def _override():
        return user
    return _override


@pytest.mark.asyncio
async def test_admin_stats_accessible_by_admin(client, admin_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(admin_user)
    app.dependency_overrides[require_admin] = make_auth_override(admin_user)
    try:
        response = await client.get("/api/v1/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_projects" in data
        assert "total_documents" in data
        assert "paying_subscribers" in data
        assert all(isinstance(v, int) for v in data.values())
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)
        app.dependency_overrides.pop(require_admin, None)


@pytest.mark.asyncio
async def test_admin_users_list(client, admin_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(admin_user)
    app.dependency_overrides[require_admin] = make_auth_override(admin_user)
    try:
        response = await client.get("/api/v1/admin/users")
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        emails = [u["email"] for u in users]
        assert "admin@example.com" in emails
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)
        app.dependency_overrides.pop(require_admin, None)


@pytest.mark.asyncio
async def test_admin_endpoint_blocked_for_regular_user(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        response = await client.get("/api/v1/admin/stats")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)
