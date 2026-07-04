"""Integration tests for semantic search endpoint."""
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.api.v1.deps import get_current_db_user
from app.main import app


def make_auth_override(user):
    async def _override():
        return user
    return _override


@pytest.mark.asyncio
async def test_semantic_search_returns_results(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Search Project"})
        project_id = proj_resp.json()["id"]

        mock_chunk = MagicMock()
        mock_chunk.id = uuid.uuid4()
        mock_chunk.filename = "research.pdf"
        mock_chunk.page_number = 5
        mock_chunk.section = "Methods"
        mock_chunk.content = "We used a novel approach to solve the problem."

        with patch(
            "app.services.rag_service.rag_service.retrieve",
            new_callable=AsyncMock,
            return_value=[{"chunk": mock_chunk, "score": 0.92}],
        ):
            response = await client.post(
                "/api/v1/search",
                json={"project_id": project_id, "query": "novel approach", "top_k": 5},
            )

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["filename"] == "research.pdf"
        assert results[0]["score"] == pytest.approx(0.92)
        assert results[0]["section"] == "Methods"
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)


@pytest.mark.asyncio
async def test_semantic_search_empty_returns_empty_list(client, test_user):
    app.dependency_overrides[get_current_db_user] = make_auth_override(test_user)
    try:
        proj_resp = await client.post("/api/v1/projects", json={"name": "Empty Search Project"})
        project_id = proj_resp.json()["id"]

        with patch(
            "app.services.rag_service.rag_service.retrieve",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = await client.post(
                "/api/v1/search",
                json={"project_id": project_id, "query": "something not found"},
            )

        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.pop(get_current_db_user, None)
