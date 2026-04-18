# Irrelevant Question Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject questions unrelated to the user's uploaded data with the lowest cost and fastest response time.

**Architecture:** Two-layer filtering — Layer 1 is a zero-cost keyword/regex heuristic that catches obviously off-topic questions before any LLM call. Layer 2 extends the existing `CHAT_CLASSIFY_PROMPT` to return `"irrelevant"` as a third question type, catching subtler cases with zero additional LLM cost (the classify call already exists). When either layer triggers, a static rejection message is returned immediately — no `format_answer` LLM call needed, saving that API cost too.

**Tech Stack:** Python (FastAPI backend), TypeScript (React frontend)

---

### Task 1: Add `IRRELEVANT` to `QuestionType` enum and `QuestionInterpretation`

**Files:**
- Modify: `server/models/domain.py:144-152`

- [ ] **Step 1: Write the failing test**

Create: `server/tests/test_question_filter.py`

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd server && python -m pytest tests/test_question_filter.py::test_question_type_has_irrelevant -v`
Expected: FAIL with `AttributeError: IRRELEVANT is not a member of QuestionType`

- [ ] **Step 3: Write minimal implementation**

In `server/models/domain.py`, add `IRRELEVANT` to the `QuestionType` enum:

```python
class QuestionType(Enum):
    COMPUTATIONAL = "computational"
    CONVERSATIONAL = "conversational"
    IRRELEVANT = "irrelevant"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd server && python -m pytest tests/test_question_filter.py -v`
Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add server/models/domain.py server/tests/test_question_filter.py
git commit -m "feat: add IRRELEVANT to QuestionType enum"
```

---

### Task 2: Add keyword-based heuristic pre-filter (Layer 1)

**Files:**
- Create: `server/llm/relevance.py`
- Test: `server/tests/test_question_filter.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `server/tests/test_question_filter.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && python -m pytest tests/test_question_filter.py::TestKeywordFilter -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'llm.relevance'`

- [ ] **Step 3: Write minimal implementation**

Create `server/llm/relevance.py`:

```python
import re

# Patterns that strongly indicate non-data questions.
# Each pattern is compiled once at import time for speed.
_IRRELEVANT_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(tell|say)\s+(me\s+)?(a\s+)?(joke|story|riddle|fun fact)",
        r"\bwrite\s+(me\s+)?(a\s+)?(poem|essay|letter|email|code|script|song|story)",
        r"\b(what('?s| is)\s+the\s+weather|forecast)\b",
        r"\bwho\s+is\s+the\s+(president|prime minister|king|queen|ceo)\b",
        r"\btranslat(e|ion)\b",
        r"\b(how\s+(do|can|to)\s+(i|you|we)\s+(cook|bake|make food|fix|repair|install|draw|paint|play))\b",
        r"\b(play|sing|dance|draw)\s+(a\s+)?(game|song|music|picture)\b",
        r"\bmeaning\s+of\s+life\b",
        r"\b(recipe|cooking|baking)\s+(for|instructions)\b",
        r"\b(help\s+me\s+)?(write|draft|compose)\s+(an?\s+)?(essay|blog|article|resume|cv|cover letter)\b",
        r"\b(what|who)\s+(is|are|was|were)\s+[A-Z][a-z]+\s+[A-Z]",  # "Who is Elon Musk"
        r"\bwrite\s+(me\s+)?python|javascript|java|html|css|sql|code\b",
    ]
]

# If the question matches ANY of these data-related patterns, it's NOT irrelevant
# even if it also matches an irrelevant pattern (safety net to avoid false positives).
_DATA_SAFEGUARD_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(data|dataset|column|row|table|chart|graph|plot|trend|sales|revenue|profit|cost|price|inventory|order|customer|product|category|region|average|total|sum|count|max|min|mean|median|percentage|proportion|share|distribution|correlation|comparison|rank|top|bottom|group\s+by|filter|sort|aggregate|breakdown)\b",
    ]
]


def is_obviously_irrelevant(question: str) -> bool:
    """Fast heuristic check. Returns True only for clearly off-topic questions.

    Designed for zero false positives on data questions (prefer letting
    ambiguous cases through to the LLM layer).
    """
    # If the question mentions data-related terms, never block it
    for pattern in _DATA_SAFEGUARD_PATTERNS:
        if pattern.search(question):
            return False

    # Check against irrelevant patterns
    for pattern in _IRRELEVANT_PATTERNS:
        if pattern.search(question):
            return True

    return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_question_filter.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add server/llm/relevance.py server/tests/test_question_filter.py
git commit -m "feat: add keyword-based irrelevant question pre-filter (Layer 1)"
```

---

### Task 3: Update `CHAT_CLASSIFY_PROMPT` to detect irrelevant questions (Layer 2)

**Files:**
- Modify: `server/llm/prompts.py:84-148`

- [ ] **Step 1: Write the failing test**

Append to `server/tests/test_question_filter.py`:

```python
from llm.prompts import CHAT_CLASSIFY_PROMPT


def test_classify_prompt_includes_irrelevant_type():
    assert '"irrelevant"' in CHAT_CLASSIFY_PROMPT
    assert "not related to the data" in CHAT_CLASSIFY_PROMPT.lower() or "unrelated" in CHAT_CLASSIFY_PROMPT.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd server && python -m pytest tests/test_question_filter.py::test_classify_prompt_includes_irrelevant_type -v`
Expected: FAIL with `AssertionError`

- [ ] **Step 3: Write minimal implementation**

In `server/llm/prompts.py`, modify the `CHAT_CLASSIFY_PROMPT`. Change the `question_type` line and add classification rules:

Replace:
```python
  "question_type": "computational" or "conversational",
```
With:
```python
  "question_type": "computational" or "conversational" or "irrelevant",
```

Replace the existing classification rules block:
```
- Classify as "computational" if the question requires querying data (aggregations, filtering, ranking, comparisons, trends, proportions, counts)
- Classify as "conversational" if the question is interpretive (explaining charts, summarizing patterns, asking "why", general advice)
```
With:
```
- Classify as "irrelevant" if the question is unrelated to the uploaded data (e.g., jokes, recipes, general knowledge, coding help, personal advice, weather, politics, creative writing). Set plan to null for irrelevant questions.
- Classify as "computational" if the question requires querying data (aggregations, filtering, ranking, comparisons, trends, proportions, counts)
- Classify as "conversational" if the question is interpretive (explaining charts, summarizing patterns, asking "why", general advice about the data)
```

Also add after `- If "conversational", set plan to null`:
```
- If "irrelevant", set plan to null
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd server && python -m pytest tests/test_question_filter.py::test_classify_prompt_includes_irrelevant_type -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/llm/prompts.py server/tests/test_question_filter.py
git commit -m "feat: extend CHAT_CLASSIFY_PROMPT to detect irrelevant questions (Layer 2)"
```

---

### Task 4: Add rejection constant and update `parse_question_interpretation`

**Files:**
- Modify: `server/llm/client.py:88-138`
- Create: `server/llm/constants.py`

- [ ] **Step 1: Write the failing test**

Append to `server/tests/test_question_filter.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd server && python -m pytest tests/test_question_filter.py::test_parse_irrelevant_question tests/test_question_filter.py::test_rejection_message_exists -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'llm.constants'`

- [ ] **Step 3: Write minimal implementation**

Create `server/llm/constants.py`:

```python
IRRELEVANT_REJECTION_MESSAGE = (
    "I can only help with questions about your uploaded data. "
    "Try asking about trends, totals, comparisons, or other insights from your dataset."
)
```

No changes needed to `parse_question_interpretation` — it already uses `QuestionType(data["question_type"])` which will resolve `"irrelevant"` to `QuestionType.IRRELEVANT` now that Task 1 added it.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_question_filter.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add server/llm/constants.py server/tests/test_question_filter.py
git commit -m "feat: add IRRELEVANT_REJECTION_MESSAGE constant"
```

---

### Task 5: Wire both layers into the `/api/chat` endpoint

**Files:**
- Modify: `server/main.py:269-406`

- [ ] **Step 1: Write the failing test**

Append to `server/tests/test_question_filter.py`:

```python
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
            # interpret_question was called (Layer 1 didn't catch this)
            mock_client.interpret_question.assert_called_once()
            # format_answer should NOT have been called
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && python -m pytest tests/test_question_filter.py::TestChatEndpointIrrelevant -v`
Expected: FAIL — the chat endpoint doesn't check irrelevance yet

- [ ] **Step 3: Write minimal implementation**

In `server/main.py`, add imports at the top (after existing imports):

```python
from llm.relevance import is_obviously_irrelevant
from llm.constants import IRRELEVANT_REJECTION_MESSAGE
```

Then, in the `chat` function, add the two-layer check right after the `client is None` check (after line 287) and before `session.chat_history.append(...)` (line 289):

```python
    # --- Layer 1: zero-cost keyword heuristic ---
    if is_obviously_irrelevant(request.question):
        rejection = IRRELEVANT_REJECTION_MESSAGE
        session.chat_history.append(Message(role="user", content=request.question))
        session.chat_history.append(Message(role="assistant", content=rejection))
        session_store.update(request.session_id, session)
        return ChatResponse(answer=rejection)
```

Then, after the `interpret_question` call (line 292-296), add Layer 2 check before the computational branch:

```python
        # --- Layer 2: LLM classified as irrelevant ---
        if interpretation.question_type == QuestionType.IRRELEVANT:
            rejection = IRRELEVANT_REJECTION_MESSAGE
            session.chat_history.append(Message(role="assistant", content=rejection))
            session_store.update(request.session_id, session)
            return ChatResponse(answer=rejection)
```

Also add `QuestionType` to the import from `models.domain` if not already there (it is already imported on line 26).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_question_filter.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add server/main.py server/tests/test_question_filter.py
git commit -m "feat: wire irrelevant question filter into /api/chat endpoint"
```

---

### Task 6: Handle rejection gracefully in the frontend

**Files:**
- Modify: `client/src/components/shared/ChatMessage.tsx:1-33`

The frontend already renders assistant messages as-is, so the rejection message will display correctly without code changes. However, we should add a subtle visual distinction so users can tell it's a system boundary message rather than a data answer.

- [ ] **Step 1: Write the failing test (manual verification)**

No automated frontend test infrastructure exists. This is a visual verification step.

Expected behavior: When user asks "tell me a joke", the assistant message should display the rejection text in the existing assistant bubble style. No chart should appear.

- [ ] **Step 2: Verify the response format is compatible**

The `ChatResponse` returned for irrelevant questions has `answer: str, chart: None` — this already matches the existing `ChatResponse` model and the frontend's `ChatResponse` type. No frontend code changes are needed.

Run the dev server and test manually:
```bash
# Terminal 1: start backend
cd server && python -m uvicorn main:app --reload --port 8000

# Terminal 2: start frontend
cd client && npm run dev
```

Upload a file, then ask "tell me a joke" in the chat. Verify:
- The rejection message appears as a normal assistant message
- No loading spinner hangs
- No error is shown
- You can still ask data questions afterward

- [ ] **Step 3: Commit (no code changes needed)**

No commit needed — frontend handles this natively.

---

### Task 7: Add `__init__.py` for test discovery and run full test suite

**Files:**
- Create: `server/tests/__init__.py`

- [ ] **Step 1: Create test init**

```python
# server/tests/__init__.py
```

(Empty file for pytest discovery)

- [ ] **Step 2: Run the full test suite**

Run: `cd server && python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add server/tests/__init__.py
git commit -m "chore: add tests __init__.py for pytest discovery"
```
