from io import BytesIO

import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

from main import app


def _make_csv(data: dict) -> bytes:
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_upload_two_csv_files():
    sales_csv = _make_csv({"product": ["A", "B"], "sales": [100, 200]})
    inventory_csv = _make_csv({"product": ["A", "B"], "stock": [50, 30]})

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/upload",
            files=[
                ("files", ("sales.csv", sales_csv, "text/csv")),
                ("files", ("inventory.csv", inventory_csv, "text/csv")),
            ],
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) == 2
    assert len(data["profiles"]) == 2

    file_names = {f["name"] for f in data["files"]}
    assert "sales.csv" in file_names
    assert "inventory.csv" in file_names


@pytest.mark.anyio
async def test_upload_mixed_valid_invalid():
    """If one file is invalid, the entire upload fails."""
    sales_csv = _make_csv({"product": ["A"], "sales": [100]})

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/upload",
            files=[
                ("files", ("sales.csv", sales_csv, "text/csv")),
                ("files", ("doc.pdf", b"fake", "application/pdf")),
            ],
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_FORMAT"


@pytest.mark.anyio
async def test_profiles_have_correct_source():
    sales_csv = _make_csv({"month": ["Jan"], "revenue": [1000]})
    costs_csv = _make_csv({"month": ["Jan"], "cost": [500]})

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/upload",
            files=[
                ("files", ("sales.csv", sales_csv, "text/csv")),
                ("files", ("costs.csv", costs_csv, "text/csv")),
            ],
        )

    data = response.json()
    profiles = data["profiles"]

    sales_profile = next(p for p in profiles if p["file_name"] == "sales.csv")
    costs_profile = next(p for p in profiles if p["file_name"] == "costs.csv")

    assert "revenue" in [c["name"] for c in sales_profile["columns"]]
    assert "cost" in [c["name"] for c in costs_profile["columns"]]
