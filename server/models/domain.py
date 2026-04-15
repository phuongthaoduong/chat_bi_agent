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


@dataclass
class SessionData:
    files: list[ParsedFile]
    profiles: list[SheetProfile]
    chat_history: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed_at: datetime = field(default_factory=datetime.now)
    memory_bytes: int = 0
