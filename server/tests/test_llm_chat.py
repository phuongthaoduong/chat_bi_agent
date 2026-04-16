import json

import pytest

from llm.client import parse_question_interpretation
from models.domain import AnalysisIntent, QuestionType


def test_parse_computational_question():
    raw = json.dumps(
        {
            "question_type": "computational",
            "plan": {
                "source": {"file_name": "sales.csv", "sheet_name": "Sheet1"},
                "intent": "top_n",
                "target_fields": ["sales"],
                "group_by": ["product"],
                "filters": None,
                "sort": {"field": "sales", "direction": "desc"},
                "limit": 5,
                "chart": {
                    "chart_type": "bar",
                    "title": "Top 5 Products",
                    "x_axis": "product",
                    "y_axis": "sales",
                },
            },
        }
    )
    result = parse_question_interpretation(raw)
    assert result.question_type == QuestionType.COMPUTATIONAL
    assert result.plan is not None
    assert result.plan.intent == AnalysisIntent.TOP_N
    assert result.plan.limit == 5


def test_parse_conversational_question():
    raw = json.dumps(
        {
            "question_type": "conversational",
            "plan": None,
        }
    )
    result = parse_question_interpretation(raw)
    assert result.question_type == QuestionType.CONVERSATIONAL
    assert result.plan is None


def test_parse_invalid_json():
    with pytest.raises(ValueError, match="Invalid"):
        parse_question_interpretation("not json")
