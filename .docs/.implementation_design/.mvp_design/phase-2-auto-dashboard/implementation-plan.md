# Phase 2: Auto Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After uploading files, the user sees an auto-generated dashboard with charts and text insights powered by DeepSeek.

**Architecture:** DeepSeek produces structured AnalysisPlans. Analysis Engine executes plans on DataFrames. Client renders charts with ECharts.

**Tech Stack:** DeepSeek API (OpenAI-compatible), pandas, ECharts (echarts-for-react)

**Depends on:** Phase 1 completed

---

## What the User Can Test After This Phase

1. Upload a CSV/Excel file → see 3-5 auto-generated charts
2. See text insight cards (e.g., "Total revenue is $45K")
3. Charts are interactive (tooltips, hover effects)
4. Different data files produce different, relevant charts

---

## File Structure (New/Modified)

### Server

```
server/
├── models/
│   └── domain.py               # Add: AnalysisPlan, AnalysisIntent, FilterCondition, etc.
├── analysis/
│   ├── __init__.py
│   └── engine.py               # AnalysisEngine
├── llm/
│   ├── __init__.py
│   ├── client.py               # LLMClient (DeepSeek)
│   └── prompts.py              # Prompt templates
└── main.py                     # Modify: wire up LLM + analysis in upload endpoint
```

### Client

```
client/src/
├── components/
│   ├── session/
│   │   ├── SessionScreen.tsx   # Modify: render dashboard
│   │   └── DashboardView.tsx   # NEW
│   └── shared/
│       ├── Chart.tsx           # NEW: ECharts wrapper
│       ├── ChartCard.tsx       # NEW
│       └── InsightCard.tsx     # NEW
└── types.ts                    # Modify: add chart types
```

---

## Tasks

### Task 1: Analysis Domain Models

**Files:**
- Modify: `server/models/domain.py`

- [ ] **Step 1: Add analysis types to domain.py**

Append to `server/models/domain.py`:
```python
class AnalysisIntent(Enum):
    AGGREGATE = "aggregate"
    DISTRIBUTION = "distribution"
    TREND = "trend"
    COMPARISON = "comparison"
    TOP_N = "top_n"
    CORRELATION = "correlation"


@dataclass
class FilterCondition:
    field: str
    operator: str  # "eq", "ne", "gt", "lt", "gte", "lte", "in", "contains"
    value: Any


@dataclass
class SortSpec:
    field: str
    direction: str  # "asc", "desc"


@dataclass
class ChartSpec:
    chart_type: str  # "bar", "line", "pie", "scatter"
    title: str
    x_axis: str | None = None
    y_axis: str | None = None


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


class ResultType(Enum):
    TABULAR = "tabular"
    SCALAR = "scalar"
    LIST = "list"


@dataclass
class TabularResult:
    columns: list[str]
    rows: list[list[Any]]


@dataclass
class ScalarResult:
    label: str
    value: Any


@dataclass
class ListResult:
    items: list[dict[str, Any]]


@dataclass
class ChartData:
    chart_type: str
    title: str
    labels: list[str]
    datasets: list[dict[str, Any]]
    x_axis: str | None = None
    y_axis: str | None = None


@dataclass
class AnalysisResult:
    result_type: ResultType
    data: TabularResult | ScalarResult | ListResult
    chart_data: ChartData | None = None


@dataclass
class DashboardSuggestion:
    insights: list[str]
    plans: list[AnalysisPlan]
```

- [ ] **Step 2: Commit**

```bash
git add server/models/domain.py
git commit -m "feat: add analysis plan and result domain models"
```

---

### Task 2: Analysis Engine

**Files:**
- Create: `server/analysis/__init__.py`
- Create: `server/analysis/engine.py`
- Create: `server/tests/test_analysis_engine.py`

- [ ] **Step 1: Write the failing tests**

Create `server/tests/test_analysis_engine.py`:
```python
import pandas as pd
import pytest

from analysis.engine import AnalysisEngine
from models.domain import (
    AnalysisIntent,
    AnalysisPlan,
    ChartSpec,
    DataSource,
    FilterCondition,
    ResultType,
    SheetData,
    SortSpec,
)

SOURCE = DataSource(file_name="test.csv", sheet_name="Sheet1")


def _make_sales_data() -> list[SheetData]:
    df = pd.DataFrame(
        {
            "month": ["Jan", "Feb", "Mar", "Jan", "Feb", "Mar"],
            "product": ["A", "A", "A", "B", "B", "B"],
            "sales": [100, 150, 200, 80, 120, 160],
            "region": ["North", "North", "South", "South", "North", "South"],
        }
    )
    return [SheetData(name="Sheet1", df=df)]


def test_aggregate_sum():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["sales"],
        group_by=["product"],
    )
    result = engine.execute_plan(plan, _make_sales_data())

    assert result.result_type == ResultType.LIST
    items = result.data.items
    assert len(items) == 2
    product_a = next(i for i in items if i["label"] == "A")
    assert product_a["value"] == 450


def test_top_n():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.TOP_N,
        target_fields=["sales"],
        group_by=["month"],
        sort=SortSpec(field="sales", direction="desc"),
        limit=2,
    )
    result = engine.execute_plan(plan, _make_sales_data())

    assert result.result_type == ResultType.LIST
    assert len(result.data.items) == 2
    assert result.data.items[0]["label"] == "Mar"


def test_distribution():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.DISTRIBUTION,
        target_fields=["region"],
    )
    result = engine.execute_plan(plan, _make_sales_data())

    assert result.result_type == ResultType.LIST
    items = result.data.items
    assert any(i["label"] == "North" for i in items)


def test_filter():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["sales"],
        group_by=["product"],
        filters=[FilterCondition(field="region", operator="eq", value="North")],
    )
    result = engine.execute_plan(plan, _make_sales_data())

    items = result.data.items
    product_a = next(i for i in items if i["label"] == "A")
    assert product_a["value"] == 250  # Jan(100) + Feb(150)


def test_chart_data_generated():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["sales"],
        group_by=["product"],
        chart=ChartSpec(chart_type="bar", title="Sales by Product"),
    )
    result = engine.execute_plan(plan, _make_sales_data())

    assert result.chart_data is not None
    assert result.chart_data.chart_type == "bar"
    assert result.chart_data.title == "Sales by Product"
    assert len(result.chart_data.labels) == 2


def test_invalid_source_raises():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=DataSource(file_name="missing.csv", sheet_name="Sheet1"),
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["sales"],
    )
    with pytest.raises(ValueError, match="not found"):
        engine.execute_plan(plan, _make_sales_data())


def test_invalid_column_raises():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["nonexistent"],
    )
    with pytest.raises(ValueError, match="column"):
        engine.execute_plan(plan, _make_sales_data())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && python -m pytest tests/test_analysis_engine.py -v`
Expected: FAIL

- [ ] **Step 3: Implement AnalysisEngine**

Create `server/analysis/engine.py`:
```python
import pandas as pd

from models.domain import (
    AnalysisIntent,
    AnalysisPlan,
    AnalysisResult,
    ChartData,
    FilterCondition,
    ListResult,
    ResultType,
    ScalarResult,
    SheetData,
    TabularResult,
)


class AnalysisEngine:
    def execute_plan(
        self, plan: AnalysisPlan, sheets: list[SheetData]
    ) -> AnalysisResult:
        df = self._resolve_source(plan, sheets)
        df = self._apply_filters(df, plan.filters)

        if plan.intent == AnalysisIntent.AGGREGATE:
            result = self._aggregate(df, plan)
        elif plan.intent == AnalysisIntent.DISTRIBUTION:
            result = self._distribution(df, plan)
        elif plan.intent == AnalysisIntent.TREND:
            result = self._trend(df, plan)
        elif plan.intent == AnalysisIntent.COMPARISON:
            result = self._comparison(df, plan)
        elif plan.intent == AnalysisIntent.TOP_N:
            result = self._top_n(df, plan)
        elif plan.intent == AnalysisIntent.CORRELATION:
            result = self._correlation(df, plan)
        else:
            raise ValueError(f"Unknown intent: {plan.intent}")

        chart_data = self._build_chart_data(result, plan) if plan.chart else None

        return AnalysisResult(
            result_type=result[0],
            data=result[1],
            chart_data=chart_data,
        )

    def _resolve_source(
        self, plan: AnalysisPlan, sheets: list[SheetData]
    ) -> pd.DataFrame:
        for sheet in sheets:
            if sheet.name == plan.source.sheet_name:
                self._validate_columns(sheet.df, plan)
                return sheet.df.copy()
        raise ValueError(
            f"Dataset not found: {plan.source.file_name} / {plan.source.sheet_name}"
        )

    def _validate_columns(self, df: pd.DataFrame, plan: AnalysisPlan) -> None:
        all_fields = set(plan.target_fields)
        if plan.group_by:
            all_fields.update(plan.group_by)
        if plan.filters:
            all_fields.update(f.field for f in plan.filters)
        if plan.sort:
            all_fields.add(plan.sort.field)

        missing = all_fields - set(df.columns)
        if missing:
            raise ValueError(f"Invalid column(s): {', '.join(sorted(missing))}")

    def _apply_filters(
        self, df: pd.DataFrame, filters: list[FilterCondition] | None
    ) -> pd.DataFrame:
        if not filters:
            return df

        for f in filters:
            if f.operator == "eq":
                df = df[df[f.field] == f.value]
            elif f.operator == "ne":
                df = df[df[f.field] != f.value]
            elif f.operator == "gt":
                df = df[df[f.field] > f.value]
            elif f.operator == "lt":
                df = df[df[f.field] < f.value]
            elif f.operator == "gte":
                df = df[df[f.field] >= f.value]
            elif f.operator == "lte":
                df = df[df[f.field] <= f.value]
            elif f.operator == "in":
                df = df[df[f.field].isin(f.value)]
            elif f.operator == "contains":
                df = df[df[f.field].astype(str).str.contains(str(f.value), case=False, na=False)]
        return df

    def _aggregate(
        self, df: pd.DataFrame, plan: AnalysisPlan
    ) -> tuple[ResultType, ListResult | ScalarResult]:
        target = plan.target_fields[0]

        if plan.group_by:
            grouped = df.groupby(plan.group_by)[target].sum().reset_index()
            if plan.sort:
                grouped = grouped.sort_values(
                    plan.sort.field,
                    ascending=(plan.sort.direction == "asc"),
                )
            if plan.limit:
                grouped = grouped.head(plan.limit)
            items = [
                {"label": str(row[plan.group_by[0]]), "value": self._serialize(row[target])}
                for _, row in grouped.iterrows()
            ]
            return (ResultType.LIST, ListResult(items=items))
        else:
            total = self._serialize(df[target].sum())
            return (ResultType.SCALAR, ScalarResult(label=f"Total {target}", value=total))

    def _distribution(
        self, df: pd.DataFrame, plan: AnalysisPlan
    ) -> tuple[ResultType, ListResult]:
        target = plan.target_fields[0]
        counts = df[target].value_counts()
        if plan.limit:
            counts = counts.head(plan.limit)
        items = [
            {"label": str(v), "value": int(c)} for v, c in counts.items()
        ]
        return (ResultType.LIST, ListResult(items=items))

    def _trend(
        self, df: pd.DataFrame, plan: AnalysisPlan
    ) -> tuple[ResultType, ListResult]:
        target = plan.target_fields[0]
        group_col = plan.group_by[0] if plan.group_by else target
        grouped = df.groupby(group_col)[target].sum().reset_index()
        items = [
            {"label": str(row[group_col]), "value": self._serialize(row[target])}
            for _, row in grouped.iterrows()
        ]
        return (ResultType.LIST, ListResult(items=items))

    def _comparison(
        self, df: pd.DataFrame, plan: AnalysisPlan
    ) -> tuple[ResultType, ListResult]:
        return self._aggregate(df, plan)

    def _top_n(
        self, df: pd.DataFrame, plan: AnalysisPlan
    ) -> tuple[ResultType, ListResult]:
        target = plan.target_fields[0]
        group_col = plan.group_by[0] if plan.group_by else target

        if plan.group_by:
            grouped = df.groupby(group_col)[target].sum().reset_index()
        else:
            grouped = df[[target]].copy()
            grouped[group_col] = grouped[target].astype(str)

        sort_dir = plan.sort.direction if plan.sort else "desc"
        grouped = grouped.sort_values(target, ascending=(sort_dir == "asc"))
        limit = plan.limit or 5
        grouped = grouped.head(limit)

        items = [
            {"label": str(row[group_col]), "value": self._serialize(row[target])}
            for _, row in grouped.iterrows()
        ]
        return (ResultType.LIST, ListResult(items=items))

    def _correlation(
        self, df: pd.DataFrame, plan: AnalysisPlan
    ) -> tuple[ResultType, TabularResult]:
        if len(plan.target_fields) < 2:
            raise ValueError("Correlation requires at least 2 target fields")
        f1, f2 = plan.target_fields[0], plan.target_fields[1]
        rows = [
            [self._serialize(row[f1]), self._serialize(row[f2])]
            for _, row in df[[f1, f2]].dropna().iterrows()
        ]
        return (ResultType.TABULAR, TabularResult(columns=[f1, f2], rows=rows))

    def _build_chart_data(
        self, result: tuple[ResultType, any], plan: AnalysisPlan
    ) -> ChartData:
        result_type, data = result
        labels = []
        datasets = []

        if isinstance(data, ListResult):
            labels = [item["label"] for item in data.items]
            datasets = [
                {"label": plan.target_fields[0], "data": [item["value"] for item in data.items]}
            ]
        elif isinstance(data, TabularResult):
            labels = [str(r[0]) for r in data.rows]
            datasets = [
                {"label": data.columns[1], "data": [r[1] for r in data.rows]}
            ]

        return ChartData(
            chart_type=plan.chart.chart_type,
            title=plan.chart.title,
            labels=labels,
            datasets=datasets,
            x_axis=plan.chart.x_axis,
            y_axis=plan.chart.y_axis,
        )

    def _serialize(self, value):
        if hasattr(value, "item"):
            return value.item()
        return value
```

- [ ] **Step 4: Create analysis/__init__.py**

```python
# analysis package
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_analysis_engine.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add server/analysis/ server/tests/test_analysis_engine.py
git commit -m "feat: add analysis engine with 6 intent types and validation"
```

---

### Task 3: LLM Prompts

**Files:**
- Create: `server/llm/__init__.py`
- Create: `server/llm/prompts.py`

- [ ] **Step 1: Create prompts.py**

Create `server/llm/prompts.py`:
```python
from models.domain import SheetProfile


def build_dataset_inventory(profiles: list[SheetProfile]) -> str:
    lines = []
    for p in profiles:
        col_info = ", ".join(
            f"{c.name} ({c.dtype})" for c in p.columns
        )
        lines.append(
            f'- "{p.source.file_name}" / "{p.source.sheet_name}": '
            f"columns [{col_info}] ({p.row_count} rows)"
        )
    return "\n".join(lines)


def build_profile_detail(profiles: list[SheetProfile]) -> str:
    sections = []
    for p in profiles:
        cols = []
        for c in p.columns:
            col_desc = f"  - {c.name} ({c.dtype}): {c.unique_count} unique"
            if c.stats:
                col_desc += f", stats={c.stats}"
            if c.sample_values:
                col_desc += f", samples={c.sample_values[:3]}"
            cols.append(col_desc)
        sections.append(
            f'Dataset: "{p.source.file_name}" / "{p.source.sheet_name}" '
            f"({p.row_count} rows)\n" + "\n".join(cols)
        )
    return "\n\n".join(sections)


DASHBOARD_SYSTEM_PROMPT = """You are a data analyst. Given the dataset schemas below, suggest 3-5 charts that give a business user the most useful overview.

AVAILABLE DATASETS:
{dataset_inventory}

DETAILED SCHEMA:
{profile_detail}

Respond with EXACTLY this JSON structure (no markdown, no code fences):
{{
  "insights": ["string — 1 sentence each, based on the stats provided"],
  "plans": [
    {{
      "source": {{ "file_name": "...", "sheet_name": "..." }},
      "intent": "aggregate|distribution|trend|comparison|top_n|correlation",
      "target_fields": ["column_name"],
      "group_by": ["column_name"] or null,
      "filters": null,
      "sort": {{"field": "...", "direction": "asc|desc"}} or null,
      "limit": number or null,
      "chart": {{
        "chart_type": "bar|line|pie|scatter",
        "title": "string",
        "x_axis": "column_name" or null,
        "y_axis": "column_name" or null
      }}
    }}
  ]
}}

RULES:
- Every plan MUST include a "source" specifying which dataset to query
- Only reference columns that exist in the specified dataset's schema
- Only use intents from the allowed list: aggregate, distribution, trend, comparison, top_n, correlation
- Keep insights concise (1 sentence each), grounded in the stats provided
- Suggest charts that highlight different aspects of the data
- For trend analysis, use datetime or ordered categorical columns for group_by"""
```

- [ ] **Step 2: Create llm/__init__.py**

```python
# llm package
```

- [ ] **Step 3: Commit**

```bash
git add server/llm/
git commit -m "feat: add LLM prompt templates for dashboard generation"
```

---

### Task 4: LLM Client (DeepSeek)

**Files:**
- Create: `server/llm/client.py`
- Modify: `server/config.py`
- Create: `server/tests/test_llm_client.py`

- [ ] **Step 1: Add DeepSeek config**

Add to `server/config.py`:
```python
import os

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
```

- [ ] **Step 2: Add openai to requirements.txt**

Add to `server/requirements.txt`:
```
openai==1.58.1
```

Run: `cd server && pip install openai`

- [ ] **Step 3: Write the test**

Create `server/tests/test_llm_client.py`:
```python
import json

import pytest

from llm.client import LLMClient, parse_dashboard_response
from models.domain import AnalysisIntent, DataSource, SheetProfile, ColumnProfile


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
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd server && python -m pytest tests/test_llm_client.py -v`
Expected: FAIL

- [ ] **Step 5: Implement LLMClient**

Create `server/llm/client.py`:
```python
import json
import logging

from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from llm.prompts import (
    DASHBOARD_SYSTEM_PROMPT,
    build_dataset_inventory,
    build_profile_detail,
)
from models.domain import (
    AnalysisIntent,
    AnalysisPlan,
    ChartSpec,
    DashboardSuggestion,
    DataSource,
    FilterCondition,
    SheetProfile,
    SortSpec,
)

logger = logging.getLogger(__name__)


def parse_dashboard_response(raw: str) -> DashboardSuggestion:
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}")

    if "plans" not in data:
        raise ValueError("Missing 'plans' in LLM response")

    plans = []
    for p in data["plans"]:
        source = DataSource(
            file_name=p["source"]["file_name"],
            sheet_name=p["source"]["sheet_name"],
        )
        filters = None
        if p.get("filters"):
            filters = [
                FilterCondition(field=f["field"], operator=f["operator"], value=f["value"])
                for f in p["filters"]
            ]
        sort = None
        if p.get("sort"):
            sort = SortSpec(field=p["sort"]["field"], direction=p["sort"]["direction"])

        chart = None
        if p.get("chart"):
            chart = ChartSpec(
                chart_type=p["chart"]["chart_type"],
                title=p["chart"]["title"],
                x_axis=p["chart"].get("x_axis"),
                y_axis=p["chart"].get("y_axis"),
            )

        plans.append(
            AnalysisPlan(
                source=source,
                intent=AnalysisIntent(p["intent"]),
                target_fields=p["target_fields"],
                group_by=p.get("group_by"),
                filters=filters,
                sort=sort,
                limit=p.get("limit"),
                chart=chart,
            )
        )

    return DashboardSuggestion(
        insights=data.get("insights", []),
        plans=plans,
    )


class LLMClient:
    def __init__(self):
        self._client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )

    def suggest_dashboard(
        self, profiles: list[SheetProfile]
    ) -> DashboardSuggestion:
        inventory = build_dataset_inventory(profiles)
        detail = build_profile_detail(profiles)

        prompt = DASHBOARD_SYSTEM_PROMPT.format(
            dataset_inventory=inventory,
            profile_detail=detail,
        )

        response = self._client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        raw = response.choices[0].message.content
        logger.info("LLM dashboard response: %s", raw)

        try:
            return parse_dashboard_response(raw)
        except (ValueError, KeyError) as e:
            logger.warning("First LLM parse failed (%s), retrying...", e)
            # Retry once
            response = self._client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": "Your response was not valid JSON. Please respond with ONLY the JSON structure, no markdown or code fences.",
                    },
                ],
                temperature=0.1,
            )
            raw = response.choices[0].message.content
            return parse_dashboard_response(raw)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_llm_client.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add server/llm/ server/config.py server/requirements.txt server/tests/test_llm_client.py
git commit -m "feat: add DeepSeek LLM client with dashboard suggestion parsing"
```

---

### Task 5: Wire Upload Endpoint to LLM + Analysis

**Files:**
- Modify: `server/main.py`
- Modify: `server/models/api.py`

- [ ] **Step 1: Add chart types to api.py**

Add to `server/models/api.py`:
```python
class ChartDataResponse(BaseModel):
    chart_type: str
    title: str
    labels: list
    datasets: list[dict]
    x_axis: str | None = None
    y_axis: str | None = None


class UploadResponse(BaseModel):
    session_id: str
    files: list[FileInfo]
    profiles: list[SheetProfileResponse]
    warnings: list[str]
    insights: list[str] = []
    charts: list[ChartDataResponse] = []
```

- [ ] **Step 2: Update main.py upload endpoint to generate dashboard**

Add after profiling in the upload handler:
```python
from analysis.engine import AnalysisEngine
from llm.client import LLMClient

analysis_engine = AnalysisEngine()

# Initialize LLM client (lazy — only if API key is set)
llm_client: LLMClient | None = None

def get_llm_client() -> LLMClient | None:
    global llm_client
    if llm_client is None:
        from config import DEEPSEEK_API_KEY
        if DEEPSEEK_API_KEY:
            llm_client = LLMClient()
    return llm_client
```

In the upload endpoint, after building profiles, add:
```python
    insights = []
    chart_responses = []

    client = get_llm_client()
    if client:
        try:
            suggestion = client.suggest_dashboard(all_profiles)
            insights = suggestion.insights

            for plan in suggestion.plans:
                try:
                    # Find the right sheets for this plan's source
                    target_sheets = []
                    for pf in parsed_files:
                        if pf.name == plan.source.file_name:
                            target_sheets = pf.sheets
                            break
                    if not target_sheets:
                        continue

                    result = analysis_engine.execute_plan(plan, target_sheets)
                    if result.chart_data:
                        chart_responses.append(
                            ChartDataResponse(
                                chart_type=result.chart_data.chart_type,
                                title=result.chart_data.title,
                                labels=result.chart_data.labels,
                                datasets=result.chart_data.datasets,
                                x_axis=result.chart_data.x_axis,
                                y_axis=result.chart_data.y_axis,
                            )
                        )
                except Exception as e:
                    import logging
                    logging.warning(f"Failed to execute plan: {e}")
                    continue
        except Exception as e:
            import logging
            logging.warning(f"LLM dashboard generation failed: {e}")
            # Dashboard still works without LLM — just no charts/insights
```

Update the return to include insights and charts:
```python
    return UploadResponse(
        session_id=session_id,
        files=file_infos,
        profiles=profile_responses,
        warnings=warnings,
        insights=insights,
        charts=chart_responses,
    )
```

- [ ] **Step 3: Test manually**

1. Set env: `export DEEPSEEK_API_KEY=your_key_here`
2. Start server: `cd server && uvicorn main:app --reload --port 8000`
3. Upload a file via the client
4. Check the JSON response for `insights` and `charts` arrays

- [ ] **Step 4: Commit**

```bash
git add server/main.py server/models/api.py
git commit -m "feat: wire upload endpoint to DeepSeek dashboard generation"
```

---

### Task 6: Client Chart Components

**Files:**
- Create: `client/src/components/shared/Chart.tsx`
- Create: `client/src/components/shared/ChartCard.tsx`
- Create: `client/src/components/shared/InsightCard.tsx`
- Modify: `client/src/types.ts`

Install ECharts:
```bash
cd client && npm install echarts echarts-for-react
```

- [ ] **Step 1: Add chart types to types.ts**

Add to `client/src/types.ts`:
```typescript
export interface ChartDataset {
  label: string;
  data: number[];
}

export interface ChartData {
  chart_type: string;
  title: string;
  labels: string[];
  datasets: ChartDataset[];
  x_axis?: string | null;
  y_axis?: string | null;
}

export interface UploadResponse {
  session_id: string;
  files: FileInfo[];
  profiles: SheetProfile[];
  warnings: string[];
  insights: string[];
  charts: ChartData[];
}
```

- [ ] **Step 2: Create Chart.tsx (ECharts wrapper)**

Create `client/src/components/shared/Chart.tsx`:
```tsx
import ReactECharts from "echarts-for-react";
import { ChartData } from "../../types";

interface ChartProps {
  data: ChartData;
  height?: number;
}

export function Chart({ data, height = 300 }: ChartProps) {
  const option = buildOption(data);
  return <ReactECharts option={option} style={{ height }} />;
}

function buildOption(data: ChartData): Record<string, unknown> {
  const { chart_type, title, labels, datasets } = data;

  if (chart_type === "pie") {
    return {
      title: { text: title, left: "center" },
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: "60%",
          data: labels.map((label, i) => ({
            name: label,
            value: datasets[0]?.data[i] ?? 0,
          })),
        },
      ],
    };
  }

  if (chart_type === "scatter") {
    return {
      title: { text: title },
      tooltip: { trigger: "axis" },
      xAxis: { type: "value", name: data.x_axis || "" },
      yAxis: { type: "value", name: data.y_axis || "" },
      series: datasets.map((ds) => ({
        type: "scatter",
        name: ds.label,
        data: ds.data.map((v, i) => [labels[i], v]),
      })),
    };
  }

  // bar, line
  return {
    title: { text: title },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: labels,
      name: data.x_axis || "",
      axisLabel: { rotate: labels.length > 6 ? 30 : 0 },
    },
    yAxis: { type: "value", name: data.y_axis || "" },
    series: datasets.map((ds) => ({
      type: chart_type === "line" ? "line" : "bar",
      name: ds.label,
      data: ds.data,
    })),
  };
}
```

- [ ] **Step 3: Create ChartCard.tsx**

Create `client/src/components/shared/ChartCard.tsx`:
```tsx
import { ChartData } from "../../types";
import { Chart } from "./Chart";

interface ChartCardProps {
  data: ChartData;
}

export function ChartCard({ data }: ChartCardProps) {
  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "16px",
        backgroundColor: "white",
      }}
    >
      <Chart data={data} />
    </div>
  );
}
```

- [ ] **Step 4: Create InsightCard.tsx**

Create `client/src/components/shared/InsightCard.tsx`:
```tsx
interface InsightCardProps {
  text: string;
}

export function InsightCard({ text }: InsightCardProps) {
  return (
    <div
      style={{
        padding: "12px 16px",
        backgroundColor: "#f0f9ff",
        border: "1px solid #bae6fd",
        borderRadius: "8px",
        fontSize: "14px",
        color: "#0c4a6e",
      }}
    >
      {text}
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add client/src/components/shared/ client/src/types.ts client/package.json client/package-lock.json
git commit -m "feat: add ECharts wrapper, ChartCard, and InsightCard components"
```

---

### Task 7: Dashboard View

**Files:**
- Create: `client/src/components/session/DashboardView.tsx`
- Modify: `client/src/components/session/SessionScreen.tsx`

- [ ] **Step 1: Create DashboardView component**

Create `client/src/components/session/DashboardView.tsx`:
```tsx
import { ChartData } from "../../types";
import { ChartCard } from "../shared/ChartCard";
import { InsightCard } from "../shared/InsightCard";

interface DashboardViewProps {
  insights: string[];
  charts: ChartData[];
}

export function DashboardView({ insights, charts }: DashboardViewProps) {
  if (charts.length === 0 && insights.length === 0) {
    return (
      <div style={{ padding: "48px", textAlign: "center", color: "#9ca3af" }}>
        <p>No charts generated. Try uploading a file with more data.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "24px" }}>
      {insights.length > 0 && (
        <div
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap",
            marginBottom: "24px",
          }}
        >
          {insights.map((text, i) => (
            <InsightCard key={i} text={text} />
          ))}
        </div>
      )}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
          gap: "16px",
        }}
      >
        {charts.map((chart, i) => (
          <ChartCard key={i} data={chart} />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Update SessionScreen to render DashboardView**

Update `client/src/components/session/SessionScreen.tsx`:
```tsx
import { UploadResponse } from "../../types";
import { FileInfoBar } from "./FileInfoBar";
import { DashboardView } from "./DashboardView";

interface SessionScreenProps {
  data: UploadResponse;
  onReset: () => void;
}

export function SessionScreen({ data, onReset }: SessionScreenProps) {
  return (
    <div style={{ minHeight: "100vh" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "12px 24px",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <h1 style={{ fontSize: "20px", margin: 0 }}>ChatBI</h1>
        <button
          onClick={onReset}
          style={{
            padding: "6px 16px",
            border: "1px solid #d1d5db",
            borderRadius: "6px",
            background: "white",
            cursor: "pointer",
          }}
        >
          New Upload
        </button>
      </div>
      <FileInfoBar profiles={data.profiles} warnings={data.warnings} />
      <DashboardView insights={data.insights} charts={data.charts} />
    </div>
  );
}
```

- [ ] **Step 3: Test end-to-end**

1. Set `DEEPSEEK_API_KEY` env var
2. Start server and client
3. Upload a CSV file with meaningful data
4. Expect to see insight cards + interactive charts

- [ ] **Step 4: Commit**

```bash
git add client/src/components/session/
git commit -m "feat: add DashboardView with auto-generated charts and insights"
```

---

## Phase 2 Completion Checklist

- [ ] Upload a CSV → see 3-5 auto-generated charts with real data
- [ ] See text insight cards based on the data
- [ ] Charts are interactive (hover for tooltips)
- [ ] Upload an Excel file with multiple sheets → charts from different sheets
- [ ] Upload a different dataset → different relevant charts
- [ ] If DeepSeek API key is missing, upload still works (shows file info, no charts)
- [ ] All server tests pass: `cd server && python -m pytest -v`
