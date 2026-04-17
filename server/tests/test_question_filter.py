import pytest
from models.domain import QuestionType, QuestionInterpretation


def test_question_type_has_irrelevant():
    qt = QuestionType("irrelevant")
    assert qt == QuestionType.IRRELEVANT
    assert qt.value == "irrelevant"


def test_question_interpretation_irrelevant():
    interp = QuestionInterpretation(
        question_type=QuestionType.IRRELEVANT, plan=None
    )
    assert interp.question_type == QuestionType.IRRELEVANT
    assert interp.plan is None


from llm.relevance import is_obviously_irrelevant


class TestKeywordFilter:
    """Layer 1: zero-cost keyword heuristic."""

    @pytest.mark.parametrize("question", [
        "tell me a joke",
        "write a poem about love",
        "what's the weather in Paris",
        "who is the president of the United States",
        "can you help me write an essay",
        "translate this to French",
        "what is the meaning of life",
        "play a game with me",
        "write me Python code to sort a list",
        "how do I cook pasta",
    ])
    def test_catches_irrelevant(self, question):
        assert is_obviously_irrelevant(question) is True

    @pytest.mark.parametrize("question", [
        "what is the total revenue",
        "show me sales by region",
        "how many orders were placed",
        "which product sold the most",
        "average price per category",
        "monthly trend of revenue",
        "top 5 customers by spend",
        "what is the distribution of ages",
        "compare sales across quarters",
        "count rows where status is active",
        "what does the data show",
        "explain the chart",
        "why is revenue declining",
        "summarize the main trends",
        "tell me a joke about sales data",
        "write a poem about revenue trends",
    ])
    def test_allows_data_questions(self, question):
        assert is_obviously_irrelevant(question) is False

    @pytest.mark.parametrize("question", [
        "",
        "   ",
        "hello",
        "thanks",
    ])
    def test_ambiguous_passes_through(self, question):
        """Ambiguous or empty questions should NOT be blocked — let LLM decide."""
        assert is_obviously_irrelevant(question) is False


from llm.prompts import CHAT_CLASSIFY_PROMPT


def test_classify_prompt_includes_irrelevant_type():
    assert '"irrelevant"' in CHAT_CLASSIFY_PROMPT
    assert "not related to the data" in CHAT_CLASSIFY_PROMPT.lower() or "unrelated" in CHAT_CLASSIFY_PROMPT.lower()


import json
from llm.client import parse_question_interpretation
from llm.constants import IRRELEVANT_REJECTION_MESSAGE


def test_parse_irrelevant_question():
    raw = json.dumps({
        "question_type": "irrelevant",
        "plan": None,
    })
    result = parse_question_interpretation(raw)
    assert result.question_type == QuestionType.IRRELEVANT
    assert result.plan is None


def test_rejection_message_exists():
    assert isinstance(IRRELEVANT_REJECTION_MESSAGE, str)
    assert len(IRRELEVANT_REJECTION_MESSAGE) > 10


from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with a mock session."""
    from main import app, session_store
    from models.domain import (
        SessionData, ParsedFile, SheetData, SheetProfile,
        DataSource, ColumnProfile,
    )
    import pandas as pd

    df = pd.DataFrame({"revenue": [100, 200], "region": ["East", "West"]})
    sheet = SheetData(name="Sheet1", df=df)
    parsed = ParsedFile(name="test.xlsx", sheets=[sheet])
    profile = SheetProfile(
        source=DataSource(file_name="test.xlsx", sheet_name="Sheet1"),
        row_count=2,
        column_count=2,
        columns=[
            ColumnProfile(name="revenue", dtype="integer", null_count=0, null_pct=0.0, unique_count=2, sample_values=[100, 200], stats=None),
            ColumnProfile(name="region", dtype="categorical", null_count=0, null_pct=0.0, unique_count=2, sample_values=["East", "West"], stats=None),
        ],
    )
    session_data = SessionData(files=[parsed], profiles=[profile])
    session_store.create("test-session", session_data)

    yield TestClient(app)

    # Cleanup
    try:
        session_store._sessions.pop("test-session", None)
    except Exception:
        pass


class TestChatEndpointIrrelevant:
    def test_layer1_rejects_joke_without_llm_call(self, client):
        """Layer 1 keyword filter should reject without calling LLM at all."""
        with patch("main.get_llm_client") as mock_get_llm:
            mock_client = MagicMock()
            mock_get_llm.return_value = mock_client

            response = client.post("/api/chat", json={
                "session_id": "test-session",
                "question": "tell me a joke",
            })

            assert response.status_code == 200
            data = response.json()
            assert "only help with questions about your uploaded data" in data["answer"]
            # LLM interpret_question should NOT have been called
            mock_client.interpret_question.assert_not_called()

    def test_layer2_rejects_via_llm_classify(self, client):
        """Layer 2: LLM classifies as irrelevant, no format_answer call."""
        with patch("main.get_llm_client") as mock_get_llm:
            mock_client = MagicMock()
            mock_get_llm.return_value = mock_client
            mock_client.interpret_question.return_value = QuestionInterpretation(
                question_type=QuestionType.IRRELEVANT, plan=None,
            )

            response = client.post("/api/chat", json={
                "session_id": "test-session",
                "question": "what happened in the 2024 Olympics",
            })

            assert response.status_code == 200
            data = response.json()
            assert "only help with questions about your uploaded data" in data["answer"]
            mock_client.interpret_question.assert_called_once()
            mock_client.format_answer.assert_not_called()

    def test_data_question_passes_through(self, client):
        """Data-related questions should still work normally."""
        with patch("main.get_llm_client") as mock_get_llm:
            mock_client = MagicMock()
            mock_get_llm.return_value = mock_client
            mock_client.interpret_question.return_value = QuestionInterpretation(
                question_type=QuestionType.CONVERSATIONAL, plan=None,
            )
            mock_client.format_answer.return_value = "Revenue is growing."

            response = client.post("/api/chat", json={
                "session_id": "test-session",
                "question": "what is the total revenue",
            })

            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "Revenue is growing."
