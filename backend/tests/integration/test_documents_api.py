"""Integration tests for document upload and listing."""
import io
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.api.v1.deps import get_current_db_user
from app.main import app


def make_auth_override(user):
    async def _override():
        return user
    return _override


@pytest.fixture
def sample_txt_bytes():
    return b"This is a test document. It contains research content for testing purposes."


@pytest.mark.asyncio
async def test_upload_txt_document(client, test_user, db_session, sample_txt_bytes):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        # Create a project first
        proj_resp = await client.post("/api/v1/projects", json={"name": "Doc Test Project"})
        project_id = proj_resp.json()["id"]

        with patch("app.services.storage_service.storage_service.build_key", return_value="test/key.txt"), \
             patch("app.services.storage_service.storage_service.upload_bytes", return_value="test/key.txt"), \
             patch("app.services.ingestion_service.ingestion_service.run", new_callable=AsyncMock):

            response = await client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.txt", io.BytesIO(sample_txt_bytes), "text/plain")},
                data={"project_id": project_id},
            )

        assert response.status_code == 202
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["status"] == "pending"
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_list_documents_for_project(client, test_user, db_session, sample_txt_bytes):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "List Docs Project"})
        project_id = proj_resp.json()["id"]

        with patch("app.services.storage_service.storage_service.build_key", return_value="k"), \
             patch("app.services.storage_service.storage_service.upload_bytes", return_value="k"), \
             patch("app.services.ingestion_service.ingestion_service.run", new_callable=AsyncMock):
            await client.post(
                "/api/v1/documents/upload",
                files={"file": ("doc1.txt", io.BytesIO(sample_txt_bytes), "text/plain")},
                data={"project_id": project_id},
            )

        response = await client.get(f"/api/v1/documents/project/{project_id}")
        assert response.status_code == 200
        docs = response.json()
        assert len(docs) >= 1
        assert docs[0]["filename"] == "doc1.txt"
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_upload_unsupported_file_type(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Bad Upload Project"})
        project_id = proj_resp.json()["id"]

        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("video.mp4", io.BytesIO(b"fake"), "video/mp4")},
            data={"project_id": project_id},
        )
        assert response.status_code == 415
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_ingest_url(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "URL Project"})
        project_id = proj_resp.json()["id"]

        with patch("app.services.ingestion_service.ingestion_service.run", new_callable=AsyncMock):
            response = await client.post(
                "/api/v1/documents/ingest-url",
                json={"project_id": project_id, "url": "https://example.com/paper.html"},
            )

        assert response.status_code == 202
        data = response.json()
        assert "example.com" in data["filename"]
        assert data["status"] == "pending"
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_delete_document(client, test_user, sample_txt_bytes):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Delete Doc Project"})
        project_id = proj_resp.json()["id"]

        with patch("app.services.storage_service.storage_service.build_key", return_value="k"), \
             patch("app.services.storage_service.storage_service.upload_bytes", return_value="k"), \
             patch("app.services.storage_service.storage_service.delete", return_value=None), \
             patch("app.services.ingestion_service.ingestion_service.run", new_callable=AsyncMock):
            upload_resp = await client.post(
                "/api/v1/documents/upload",
                files={"file": ("todelete.txt", io.BytesIO(sample_txt_bytes), "text/plain")},
                data={"project_id": project_id},
            )
            doc_id = upload_resp.json()["id"]
            del_resp = await client.delete(f"/api/v1/documents/{doc_id}")
            assert del_resp.status_code == 204
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)
