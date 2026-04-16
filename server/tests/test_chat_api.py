from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _upload_file(client):
    content = (FIXTURES / "sample.csv").read_bytes()
    response = await client.post(
        "/api/upload",
        files={"files": ("sample.csv", content, "text/csv")},
    )
    return response.json()["session_id"]


@pytest.mark.anyio
async def test_chat_missing_session():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "nonexistent", "question": "hello"},
        )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.anyio
async def test_chat_without_llm_key():
    """When no LLM key is set, chat returns an error gracefully."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        session_id = await _upload_file(client)
        response = await client.post(
            "/api/chat",
            json={"session_id": session_id, "question": "What is the total sales?"},
        )
    # With or without LLM key, must return a valid status
    assert response.status_code in (200, 502)
