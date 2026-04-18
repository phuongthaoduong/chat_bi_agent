# Cross-Sheet JOIN Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow the LLM to generate an analysis plan that joins two sheets from the same file on a common key, enabling questions like "which orders were sold below wholesale cost?" that require data from multiple sheets.

**Architecture:** Add a `JoinSpec` to the domain model and `AnalysisPlan`. The engine applies a left-merge in `_resolve_source` before any filtering or aggregation, so all downstream logic is unchanged. The LLM learns to emit a `join` block in its plan JSON when cross-sheet data is needed.

**Tech Stack:** Python, pandas (merge), FastAPI, DeepSeek LLM via OpenAI-compatible client, pytest

---

## File Map

| File | Change |
|---|---|
| `server/models/domain.py` | Add `JoinSpec` dataclass; add `join: JoinSpec \| None` to `AnalysisPlan` |
| `server/analysis/engine.py` | Extract `_remap_col` helper; apply join in `_resolve_source`; normalize join columns |
| `server/llm/client.py` | Parse `join` block in `parse_question_interpretation` and `parse_dashboard_response` |
| `server/llm/prompts.py` | Add `join` field to plan JSON spec; add DETAIL INTENT rules and join examples to `CHAT_CLASSIFY_PROMPT` |
| `server/tests/test_analysis_engine.py` | Add join tests |
| `server/tests/test_llm_client.py` | Add join parsing tests |

---

## Task 1: Add `JoinSpec` to the domain model

**Files:**
- Modify: `server/models/domain.py`
- Test: `server/tests/test_analysis_engine.py`

- [ ] **Step 1: Write the failing test**

Add to `server/tests/test_analysis_engine.py`:

```python
from models.domain import JoinSpec

def test_join_spec_exists():
    j = JoinSpec(sheet_name="Purchase Orders", on="Product ID", columns=["Unit Cost (¥)"])
    assert j.sheet_name == "Purchase Orders"
    assert j.on == "Product ID"
    assert j.columns == ["Unit Cost (¥)"]

def test_analysis_plan_has_join_field():
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["sales"],
        join=JoinSpec(sheet_name="Other", on="id", columns=["cost"]),
    )
    assert plan.join is not None
    assert plan.join.sheet_name == "Other"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd server && python -m pytest tests/test_analysis_engine.py::test_join_spec_exists tests/test_analysis_engine.py::test_analysis_plan_has_join_field -v
```

Expected: `ImportError: cannot import name 'JoinSpec'`

- [ ] **Step 3: Add `JoinSpec` to `server/models/domain.py`**

Add this dataclass right before `AnalysisPlan`:

```python
@dataclass
class JoinSpec:
    sheet_name: str   # name of the sheet to join in
    on: str           # column name present in BOTH sheets (join key)
    columns: list[str]  # columns to bring in from the joined sheet
```

Add `join` field to `AnalysisPlan`:

```python
@dataclass
class AnalysisPlan:
    source: DataSource
    intent: AnalysisIntent
    target_fields: list[str]
    group_by: list[str] | None = None
    filters: list[FilterCondition] | None = None
    sort: SortSpec | None = None
    limit: int | None = None
    chart: ChartSpec | None = None
    time_grain: str | None = None
    join: JoinSpec | None = None   # ← new field
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd server && python -m pytest tests/test_analysis_engine.py::test_join_spec_exists tests/test_analysis_engine.py::test_analysis_plan_has_join_field -v
```

Expected: `PASSED` for both.

- [ ] **Step 5: Commit**

```bash
git add server/models/domain.py server/tests/test_analysis_engine.py
git commit -m "feat: add JoinSpec dataclass and join field to AnalysisPlan"
```

---

## Task 2: Apply join in the analysis engine

**Files:**
- Modify: `server/analysis/engine.py`
- Test: `server/tests/test_analysis_engine.py`

- [ ] **Step 1: Write failing tests**

Add to `server/tests/test_analysis_engine.py`:

```python
from models.domain import JoinSpec

PURCHASE_SOURCE = DataSource(file_name="test.csv", sheet_name="Purchase Orders")


def _make_join_sheets() -> list[SheetData]:
    """Sales orders + a separate Purchase Orders sheet with unit cost."""
    sales_df = pd.DataFrame({
        "Order ID": ["ORD-001", "ORD-002", "ORD-003"],
        "Product ID": ["P1", "P2", "P1"],
        "Unit Price (¥)": [100, 50, 80],
        "Salesperson": ["Alice", "Bob", "Alice"],
    })
    cost_df = pd.DataFrame({
        "Product ID": ["P1", "P2"],
        "Unit Cost (¥)": [90, 60],
    })
    return [
        SheetData(name="Sales Order", df=sales_df),
        SheetData(name="Purchase Orders", df=cost_df),
    ]


def test_join_brings_in_cost_column():
    """After join, merged df should contain Unit Cost (¥)."""
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=DataSource(file_name="test.csv", sheet_name="Sales Order"),
        intent=AnalysisIntent.DETAIL,
        target_fields=["Order ID", "Unit Price (¥)", "Unit Cost (¥)", "Salesperson"],
        join=JoinSpec(
            sheet_name="Purchase Orders",
            on="Product ID",
            columns=["Unit Cost (¥)"],
        ),
    )
    result = engine.execute_plan(plan, _make_join_sheets())
    assert result.result_type == ResultType.TABULAR
    assert "Unit Cost (¥)" in result.data.columns


def test_join_filter_below_cost():
    """Orders where Unit Price < Unit Cost should be ORD-002 only."""
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=DataSource(file_name="test.csv", sheet_name="Sales Order"),
        intent=AnalysisIntent.DETAIL,
        target_fields=["Order ID", "Unit Price (¥)", "Unit Cost (¥)", "Salesperson"],
        filters=[FilterCondition(field="Unit Price (¥)", operator="lt_col", value="Unit Cost (¥)")],
        join=JoinSpec(
            sheet_name="Purchase Orders",
            on="Product ID",
            columns=["Unit Cost (¥)"],
        ),
    )
    result = engine.execute_plan(plan, _make_join_sheets())
    assert result.result_type == ResultType.TABULAR
    order_ids = [row[result.data.columns.index("Order ID")] for row in result.data.rows]
    assert order_ids == ["ORD-002"]


def test_join_missing_sheet_raises():
    """Referencing a non-existent join sheet should raise ValueError."""
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=DataSource(file_name="test.csv", sheet_name="Sales Order"),
        intent=AnalysisIntent.DETAIL,
        target_fields=[],
        join=JoinSpec(sheet_name="Nonexistent", on="Product ID", columns=["cost"]),
    )
    with pytest.raises(ValueError, match="Join sheet not found"):
        engine.execute_plan(plan, _make_join_sheets())


def test_join_key_fuzzy_match():
    """Join key 'product_id' in plan should match 'Product ID' column in both sheets."""
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=DataSource(file_name="test.csv", sheet_name="Sales Order"),
        intent=AnalysisIntent.DETAIL,
        target_fields=[],
        join=JoinSpec(
            sheet_name="Purchase Orders",
            on="product_id",   # ← lowercase/underscore variant
            columns=["unit_cost_(¥)"],  # ← also fuzzy
        ),
    )
    result = engine.execute_plan(plan, _make_join_sheets())
    assert "Unit Cost (¥)" in result.data.columns
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd server && python -m pytest tests/test_analysis_engine.py::test_join_brings_in_cost_column tests/test_analysis_engine.py::test_join_filter_below_cost tests/test_analysis_engine.py::test_join_missing_sheet_raises tests/test_analysis_engine.py::test_join_key_fuzzy_match -v
```

Expected: all `FAILED` (join logic not yet implemented).

- [ ] **Step 3: Extract `_remap_col` helper and update `_resolve_source`**

In `server/analysis/engine.py`, extract a helper from the existing inline `remap` closure in `_normalize_plan_columns`, and use it in `_resolve_source` for join normalization:

```python
def _remap_col(self, name: str, df: pd.DataFrame) -> str:
    """Return the actual column name in df that fuzzy-matches `name`, or `name` unchanged."""
    if name in df.columns:
        return name
    key_to_actual = {self._col_key(c): c for c in df.columns}
    return key_to_actual.get(self._col_key(name), name)
```

Replace `_resolve_source` with:

```python
def _resolve_source(self, plan: AnalysisPlan, sheets: list[SheetData]) -> pd.DataFrame:
    # Find primary sheet
    df = None
    for sheet in sheets:
        if sheet.name == plan.source.sheet_name:
            df = sheet.df.copy()
            break
    if df is None:
        raise ValueError(
            f"Dataset not found: {plan.source.file_name} / {plan.source.sheet_name}"
        )

    # Apply join if specified
    if plan.join:
        join_df = None
        for sheet in sheets:
            if sheet.name == plan.join.sheet_name:
                join_df = sheet.df
                break
        if join_df is None:
            raise ValueError(f"Join sheet not found: {plan.join.sheet_name}")

        # Normalize join key against both dfs
        plan.join.on = self._remap_col(
            self._remap_col(plan.join.on, df), join_df
        )
        # Normalize join columns against the join sheet
        plan.join.columns = [self._remap_col(c, join_df) for c in plan.join.columns]

        # Build list of columns to pull from join sheet (key + requested columns, deduplicated)
        pull_cols = [plan.join.on] + [c for c in plan.join.columns if c != plan.join.on]
        pull_cols = [c for c in pull_cols if c in join_df.columns]

        # Left-merge; drop_duplicates on key to avoid row multiplication
        df = df.merge(
            join_df[pull_cols].drop_duplicates(subset=[plan.join.on]),
            on=plan.join.on,
            how="left",
        )

    self._normalize_plan_columns(df, plan)
    self._validate_columns(df, plan)
    return df
```

Also update `_normalize_plan_columns` to use `_remap_col` (replace the inline `remap` closure):

```python
def _normalize_plan_columns(self, df: pd.DataFrame, plan: AnalysisPlan) -> None:
    # ... (keep existing count-alias healing logic unchanged) ...

    plan.target_fields = [self._remap_col(f, df) for f in plan.target_fields]
    if plan.group_by:
        plan.group_by = [self._remap_col(f, df) for f in plan.group_by]
    _COL_OPS = {"lt_col", "gt_col", "lte_col", "gte_col", "eq_col"}
    if plan.filters:
        for f in plan.filters:
            f.field = self._remap_col(f.field, df)
            if f.operator in _COL_OPS and isinstance(f.value, str):
                f.value = self._remap_col(f.value, df)
    if plan.sort:
        plan.sort.field = self._remap_col(plan.sort.field, df)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd server && python -m pytest tests/test_analysis_engine.py::test_join_brings_in_cost_column tests/test_analysis_engine.py::test_join_filter_below_cost tests/test_analysis_engine.py::test_join_missing_sheet_raises tests/test_analysis_engine.py::test_join_key_fuzzy_match -v
```

Expected: all `PASSED`.

- [ ] **Step 5: Run full engine test suite to check no regressions**

```bash
cd server && python -m pytest tests/test_analysis_engine.py -v
```

Expected: all previously passing tests still `PASSED`.

- [ ] **Step 6: Commit**

```bash
git add server/analysis/engine.py server/tests/test_analysis_engine.py
git commit -m "feat: apply cross-sheet join in engine _resolve_source with fuzzy key normalization"
```

---

## Task 3: Parse `join` from LLM response JSON

**Files:**
- Modify: `server/llm/client.py`
- Test: `server/tests/test_llm_client.py`

- [ ] **Step 1: Write failing tests**

Add to `server/tests/test_llm_client.py`:

```python
from llm.client import parse_question_interpretation
from models.domain import JoinSpec

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd server && python -m pytest tests/test_llm_client.py::test_parse_question_interpretation_with_join tests/test_llm_client.py::test_parse_question_interpretation_without_join -v
```

Expected: `FAILED` — `parse_question_interpretation` doesn't import or handle `JoinSpec` yet.

- [ ] **Step 3: Update `server/llm/client.py`**

Add `JoinSpec` to the import from `models.domain`:

```python
from models.domain import (
    AnalysisIntent,
    AnalysisPlan,
    AnalysisResult,
    ChartSpec,
    DashboardSuggestion,
    DataSource,
    FilterCondition,
    JoinSpec,        # ← new
    Message,
    QuestionInterpretation,
    QuestionType,
    SheetProfile,
    SortSpec,
)
```

Add a `_parse_join` helper function (above `parse_dashboard_response`):

```python
def _parse_join(p: dict) -> JoinSpec | None:
    """Parse the optional 'join' block from a plan dict. Returns None if absent."""
    j = p.get("join")
    if not j:
        return None
    return JoinSpec(
        sheet_name=j["sheet_name"],
        on=j["on"],
        columns=j.get("columns") or [],
    )
```

In `parse_dashboard_response`, add `join=_parse_join(p)` to the `AnalysisPlan(...)` constructor call.

In `parse_question_interpretation`, add `join=_parse_join(p)` to the `AnalysisPlan(...)` constructor call.

Both constructors currently end with `time_grain=p.get("time_grain")`. Change to:

```python
plan = AnalysisPlan(
    source=source,
    intent=AnalysisIntent(p["intent"]),
    target_fields=p["target_fields"],
    group_by=p.get("group_by"),
    filters=filters,
    sort=sort,
    limit=p.get("limit"),
    chart=chart,
    time_grain=p.get("time_grain"),
    join=_parse_join(p),   # ← new
)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd server && python -m pytest tests/test_llm_client.py::test_parse_question_interpretation_with_join tests/test_llm_client.py::test_parse_question_interpretation_without_join -v
```

Expected: both `PASSED`.

- [ ] **Step 5: Run full client test suite to check no regressions**

```bash
cd server && python -m pytest tests/test_llm_client.py -v
```

Expected: all previously passing tests still `PASSED`.

- [ ] **Step 6: Commit**

```bash
git add server/llm/client.py server/tests/test_llm_client.py
git commit -m "feat: parse join spec from LLM response JSON"
```

---

## Task 4: Teach the LLM about joins in `CHAT_CLASSIFY_PROMPT`

**Files:**
- Modify: `server/llm/prompts.py`

No unit tests for prompt text — correctness is verified by end-to-end manual test at the end.

- [ ] **Step 1: Add `join` to the plan JSON spec in `CHAT_CLASSIFY_PROMPT`**

Find the plan JSON block inside `CHAT_CLASSIFY_PROMPT` and add `join` after `"source"`:

```python
    "plan": {{
      "source": {{ "file_name": "...", "sheet_name": "..." }},
      "join": {{
        "sheet_name": "...",
        "on": "column_name_present_in_both_sheets",
        "columns": ["column_to_bring_in"]
      }} or null,
      "intent": "aggregate|average|count|detail|distribution|trend|comparison|top_n|correlation",
      ...
    }}
```

- [ ] **Step 2: Add JOIN RULES to `CHAT_CLASSIFY_PROMPT`**

After the existing `DETAIL INTENT` rules block, add:

```
- JOIN RULE — use "join" in the plan when the question requires a column that exists in a DIFFERENT sheet from the primary source:
  - The primary "source" sheet is the one that has the main rows (e.g. "Sales Order" for order-level questions)
  - "join.sheet_name" is the sheet that has the extra column needed (e.g. "Purchase Orders" for cost data)
  - "join.on" MUST be a column name that appears in BOTH the source sheet and the join sheet (e.g. "Product ID")
  - "join.columns" lists only the column(s) you need from the join sheet (e.g. ["Unit Cost (¥)"])
  - After joining, the joined columns are available in filters, target_fields, and sort — use them normally
  - EXAMPLE "which orders were sold below wholesale cost, who sold them":
      source={{"sheet_name": "Sales Order"}},
      join={{"sheet_name": "Purchase Orders", "on": "Product ID", "columns": ["Unit Cost (¥)"]}},
      intent="detail",
      target_fields=["Order ID", "Unit Price (¥)", "Unit Cost (¥)", "Salesperson"],
      filters=[{{"field": "Unit Price (¥)", "operator": "lt_col", "value": "Unit Cost (¥)"}}],
      chart=null
  - EXAMPLE "average profit margin by product" (where cost is in Purchase Orders):
      source={{"sheet_name": "Sales Order"}},
      join={{"sheet_name": "Purchase Orders", "on": "Product ID", "columns": ["Unit Cost (¥)"]}},
      intent="average",
      target_fields=["Unit Price (¥)"],
      group_by=["Product Name"],
      chart_type="bar"
  - Do NOT use join if all needed columns are already in the same sheet
  - Do NOT join more than one extra sheet per plan
```

- [ ] **Step 3: Verify prompts file loads without error**

```bash
cd server && python -c "from llm.prompts import CHAT_CLASSIFY_PROMPT; print('OK', len(CHAT_CLASSIFY_PROMPT))"
```

Expected: `OK <some large number>`

- [ ] **Step 4: Commit**

```bash
git add server/llm/prompts.py
git commit -m "feat: teach LLM to emit join spec in analysis plan for cross-sheet questions"
```

---

## Task 5: End-to-end manual verification

**No code changes — verification only.**

- [ ] **Step 1: Run the full test suite**

```bash
cd server && python -m pytest tests/ -v
```

Expected: all tests pass, zero failures.

- [ ] **Step 2: Start the server**

```bash
cd server && uvicorn main:app --reload
```

- [ ] **Step 3: Upload the 4-sheet file and ask the target question**

Upload the file with sheets: Sales Order, Purchase Orders, Inventory, Financial Report.

Ask: *"Which orders were sold below wholesale cost, and who sold them? List all of them."*

Expected response: A markdown table with columns `Order ID`, `Unit Price (¥)`, `Unit Cost (¥)`, `Salesperson` — one row per qualifying order, no truncation.

- [ ] **Step 4: Ask a follow-up with no join needed**

Ask: *"What is the total revenue by salesperson?"*

Expected: Normal aggregate answer using only the Sales Order sheet — no join, no regressions.

- [ ] **Step 5: Final commit if any minor fixes were needed**

```bash
git add -p  # stage only intentional changes
git commit -m "fix: <describe any small adjustment>"
```
