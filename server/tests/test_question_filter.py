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
    ])
    def test_allows_data_questions(self, question):
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
