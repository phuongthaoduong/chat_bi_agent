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
