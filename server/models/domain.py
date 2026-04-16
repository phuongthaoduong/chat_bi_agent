from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd


@dataclass
class DataSource:
    file_name: str
    sheet_name: str


@dataclass
class SheetData:
    name: str
    df: pd.DataFrame


@dataclass
class ParsedFile:
    name: str
    sheets: list[SheetData]


@dataclass
class ColumnProfile:
    name: str
    dtype: str  # "numeric", "categorical", "datetime", "text"
    null_count: int
    null_pct: float
    unique_count: int
    sample_values: list[Any]
    stats: dict[str, Any] | None


@dataclass
class SheetProfile:
    source: DataSource
    row_count: int
    column_count: int
    columns: list[ColumnProfile]


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    chart: dict[str, Any] | None = None


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


class QuestionType(Enum):
    COMPUTATIONAL = "computational"
    CONVERSATIONAL = "conversational"


@dataclass
class QuestionInterpretation:
    question_type: QuestionType
    plan: AnalysisPlan | None  # null for conversational


@dataclass
class SessionData:
    files: list[ParsedFile]
    profiles: list[SheetProfile]
    chat_history: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed_at: datetime = field(default_factory=datetime.now)
    memory_bytes: int = 0
