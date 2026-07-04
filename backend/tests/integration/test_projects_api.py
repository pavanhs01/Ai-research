"""
Integration tests for projects endpoints.
Auth is bypassed by directly injecting a real DB user and overriding
the `get_current_db_user` dependency.
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.api.v1.deps import get_current_db_user
from app.main import app


def make_auth_override(user):
    async def _override():
        return user
    return _override


@pytest.mark.asyncio
async def test_create_project(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        response = await client.post("/api/v1/projects", json={"name": "My Research", "description": "Test project"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Research"
        assert data["description"] == "Test project"
        assert data["owner_id"] == str(test_user.id)
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_list_projects_returns_own_projects(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        await client.post("/api/v1/projects", json={"name": "Project Alpha"})
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        projects = response.json()
        assert isinstance(projects, list)
        names = [p["name"] for p in projects]
        assert "Project Alpha" in names
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_get_project_by_id(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        create_resp = await client.post("/api/v1/projects", json={"name": "Detail Project"})
        project_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["id"] == project_id
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_update_project(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        create_resp = await client.post("/api/v1/projects", json={"name": "Old Name"})
        project_id = create_resp.json()["id"]
        response = await client.patch(f"/api/v1/projects/{project_id}", json={"name": "New Name"})
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_delete_project(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        create_resp = await client.post("/api/v1/projects", json={"name": "To Delete"})
        project_id = create_resp.json()["id"]
        del_resp = await client.delete(f"/api/v1/projects/{project_id}")
        assert del_resp.status_code == 204
        get_resp = await client.get(f"/api/v1/projects/{project_id}")
        assert get_resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_get_nonexistent_project_returns_404(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        import uuid
        response = await client.get(f"/api/v1/projects/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_project_name_required(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        response = await client.post("/api/v1/projects", json={"name": ""})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)
