import json

import pytest

from llm.client import parse_dashboard_response
from models.domain import AnalysisIntent, ColumnProfile, DataSource, SheetProfile


def _make_profile() -> list[SheetProfile]:
    return [
        SheetProfile(
            source=DataSource(file_name="sales.csv", sheet_name="Sheet1"),
            row_count=100,
            column_count=3,
            columns=[
                ColumnProfile(
                    name="month",
                    dtype="categorical",
                    null_count=0,
                    null_pct=0.0,
                    unique_count=12,
                    sample_values=["Jan", "Feb", "Mar"],
                    stats={"top_values": [{"value": "Jan", "count": 10}]},
                ),
                ColumnProfile(
                    name="product",
                    dtype="categorical",
                    null_count=0,
                    null_pct=0.0,
                    unique_count=5,
                    sample_values=["Widget A", "Widget B"],
                    stats={"top_values": [{"value": "Widget A", "count": 30}]},
                ),
                ColumnProfile(
                    name="sales",
                    dtype="numeric",
                    null_count=0,
                    null_pct=0.0,
                    unique_count=80,
                    sample_values=[100, 200, 300],
                    stats={"min": 50, "max": 500, "mean": 250.0},
                ),
            ],
        )
    ]


def test_parse_dashboard_response_valid():
    raw = json.dumps(
        {
            "insights": ["Total sales average is $250"],
            "plans": [
                {
                    "source": {"file_name": "sales.csv", "sheet_name": "Sheet1"},
                    "intent": "aggregate",
                    "target_fields": ["sales"],
                    "group_by": ["month"],
                    "filters": None,
                    "sort": None,
                    "limit": None,
                    "chart": {
                        "chart_type": "bar",
                        "title": "Monthly Sales",
                        "x_axis": "month",
                        "y_axis": "sales",
                    },
                }
            ],
        }
    )
    result = parse_dashboard_response(raw)
    assert len(result.insights) == 1
    assert len(result.plans) == 1
    assert result.plans[0].intent == AnalysisIntent.AGGREGATE
    assert result.plans[0].source.file_name == "sales.csv"


def test_parse_dashboard_response_invalid_json():
    with pytest.raises(ValueError, match="Invalid"):
        parse_dashboard_response("not json")


def test_parse_dashboard_response_missing_fields():
    with pytest.raises(ValueError):
        parse_dashboard_response(json.dumps({"insights": []}))
