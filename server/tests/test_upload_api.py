from io import BytesIO
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_upload_csv():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        content = (FIXTURES / "sample.csv").read_bytes()
        response = await client.post(
            "/api/upload",
            files={"files": ("sample.csv", content, "text/csv")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["files"]) == 1
    assert data["files"][0]["name"] == "sample.csv"
    assert data["files"][0]["rows"] == 5
    assert len(data["profiles"]) == 1


@pytest.mark.anyio
async def test_upload_unsupported_format():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/upload",
            files={"files": ("doc.pdf", b"fake content", "application/pdf")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_FORMAT"


@pytest.mark.anyio
async def test_upload_empty_file():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/upload",
            files={"files": ("empty.csv", b"", "text/csv")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_FILE"
