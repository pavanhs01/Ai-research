"""Integration tests for RAG chat and conversation history."""
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.api.v1.deps import get_current_db_user
from app.main import app
from app.schemas.chat import Citation


def make_auth_override(user):
    async def _override():
        return user
    return _override


@pytest.mark.asyncio
async def test_chat_creates_new_conversation(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Chat Project"})
        assert proj_resp.status_code == 201
        project_id = proj_resp.json()["id"]

        mock_citations = [
            Citation(
                chunk_id=uuid.uuid4(),
                filename="paper.pdf",
                page_number=3,
                section="Results",
                snippet="The results show significant improvement.",
            )
        ]

        with patch(
            "app.services.rag_service.rag_service.answer",
            new_callable=AsyncMock,
            return_value=("Here is the answer based on the documents.", mock_citations),
        ):
            response = await client.post(
                "/api/v1/chat",
                json={"project_id": project_id, "message": "What are the main findings?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Here is the answer based on the documents."
        assert len(data["citations"]) == 1
        assert data["citations"][0]["filename"] == "paper.pdf"
        assert "conversation_id" in data
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_chat_continues_existing_conversation(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Continuation Project"})
        project_id = proj_resp.json()["id"]

        with patch("app.services.rag_service.rag_service.answer", new_callable=AsyncMock, return_value=("First answer.", [])):
            first = await client.post("/api/v1/chat", json={"project_id": project_id, "message": "First question"})
        assert first.status_code == 200
        conversation_id = first.json()["conversation_id"]

        with patch("app.services.rag_service.rag_service.answer", new_callable=AsyncMock, return_value=("Second answer.", [])):
            second = await client.post(
                "/api/v1/chat",
                json={"project_id": project_id, "conversation_id": conversation_id, "message": "Follow-up"},
            )

        assert second.status_code == 200
        assert second.json()["conversation_id"] == conversation_id
        assert second.json()["answer"] == "Second answer."
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_list_conversations(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Conv List Project"})
        project_id = proj_resp.json()["id"]

        with patch("app.services.rag_service.rag_service.answer", new_callable=AsyncMock, return_value=("ans", [])):
            r1 = await client.post("/api/v1/chat", json={"project_id": project_id, "message": "Q1"})
            r2 = await client.post("/api/v1/chat", json={"project_id": project_id, "message": "Q2"})
        assert r1.status_code == 200
        assert r2.status_code == 200

        response = await client.get(f"/api/v1/chat/conversations/{project_id}")
        assert response.status_code == 200
        convs = response.json()
        assert len(convs) >= 2
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_get_conversation_detail(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Detail Conv Project"})
        project_id = proj_resp.json()["id"]

        with patch("app.services.rag_service.rag_service.answer", new_callable=AsyncMock, return_value=("ans", [])):
            chat_resp = await client.post("/api/v1/chat", json={"project_id": project_id, "message": "Hello"})
        assert chat_resp.status_code == 200
        conv_id = chat_resp.json()["conversation_id"]

        # Get conversation detail — this triggers the relationship load
        response = await client.get(f"/api/v1/chat/conversations/detail/{conv_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv_id
        assert "messages" in data
        assert len(data["messages"]) == 2  # user + assistant
        roles = [m["role"] for m in data["messages"]]
        assert "user" in roles
        assert "assistant" in roles
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_rename_conversation(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Rename Conv Project"})
        project_id = proj_resp.json()["id"]

        with patch("app.services.rag_service.rag_service.answer", new_callable=AsyncMock, return_value=("ans", [])):
            chat_resp = await client.post("/api/v1/chat", json={"project_id": project_id, "message": "Hello"})
        conv_id = chat_resp.json()["conversation_id"]

        response = await client.patch(
            f"/api/v1/chat/conversations/{conv_id}", json={"title": "Renamed conversation"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Renamed conversation"
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_delete_conversation(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Delete Conv Project"})
        project_id = proj_resp.json()["id"]

        with patch("app.services.rag_service.rag_service.answer", new_callable=AsyncMock, return_value=("ans", [])):
            chat_resp = await client.post("/api/v1/chat", json={"project_id": project_id, "message": "Hello"})
        conv_id = chat_resp.json()["conversation_id"]

        response = await client.delete(f"/api/v1/chat/conversations/{conv_id}")
        assert response.status_code == 204

        follow_up = await client.get(f"/api/v1/chat/conversations/detail/{conv_id}")
        assert follow_up.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_delete_conversation_blocked_for_non_owner(client, test_user, admin_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Owner Conv Project"})
        project_id = proj_resp.json()["id"]

        with patch("app.services.rag_service.rag_service.answer", new_callable=AsyncMock, return_value=("ans", [])):
            chat_resp = await client.post("/api/v1/chat", json={"project_id": project_id, "message": "Hello"})
        conv_id = chat_resp.json()["conversation_id"]
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)

    app.dependency_overrides[get_current_db_user] = make_auth_override(admin_user)
    try:
        response = await client.delete(f"/api/v1/chat/conversations/{conv_id}")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)
