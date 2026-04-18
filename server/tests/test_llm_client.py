import json

import pytest

from llm.client import parse_dashboard_response, parse_question_interpretation
from models.domain import AnalysisIntent, ColumnProfile, DataSource, JoinSpec, SheetProfile


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
            "plan": {
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
            },
        }
    )
    result = parse_dashboard_response(raw)
    assert len(result.insights) == 1
    assert result.plan is not None
    assert result.plan.intent == AnalysisIntent.AGGREGATE
    assert result.plan.source.file_name == "sales.csv"


def test_parse_dashboard_response_invalid_json():
    with pytest.raises(ValueError, match="Invalid"):
        parse_dashboard_response("not json")


def test_parse_dashboard_response_missing_fields():
    """A plan object missing required keys (e.g. 'source') should raise KeyError."""
    with pytest.raises(KeyError):
        parse_dashboard_response(json.dumps({"insights": [], "plan": {"intent": "aggregate"}}))


def test_parse_question_interpretation_with_join():
    raw = json.dumps({
        "question_type": "computational",
        "plan": {
            "source": {"file_name": "data.xlsx", "sheet_name": "Sales Order"},
            "join": {
                "sheet_name": "Purchase Orders",
                "on": "Product ID",
                "columns": ["Unit Cost (¥)"]
            },
            "intent": "detail",
            "target_fields": ["Order ID", "Unit Price (¥)", "Unit Cost (¥)", "Salesperson"],
            "group_by": None,
            "filters": [
                {"field": "Unit Price (¥)", "operator": "lt_col", "value": "Unit Cost (¥)"}
            ],
            "sort": None,
            "limit": None,
            "chart": None,
        }
    })
    result = parse_question_interpretation(raw)
    assert result.plan is not None
    assert result.plan.join is not None
    assert result.plan.join.sheet_name == "Purchase Orders"
    assert result.plan.join.on == "Product ID"
    assert result.plan.join.columns == ["Unit Cost (¥)"]


def test_parse_question_interpretation_without_join():
    """Existing plans without join field should parse cleanly with join=None."""
    raw = json.dumps({
        "question_type": "computational",
        "plan": {
            "source": {"file_name": "sales.csv", "sheet_name": "Sheet1"},
            "intent": "aggregate",
            "target_fields": ["sales"],
            "group_by": ["month"],
            "filters": None,
            "sort": None,
            "limit": None,
            "chart": None,
        }
    })
    result = parse_question_interpretation(raw)
    assert result.plan is not None
    assert result.plan.join is None
