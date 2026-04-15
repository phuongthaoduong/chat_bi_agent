# Phase 1: Upload & Parse — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** User can upload CSV/Excel files and see file structure — column names, types, row counts, and basic statistics.

**Architecture:** FastAPI server with file parsers + data profiler + in-memory session store. React/Vite client with upload UI and file info display.

**Tech Stack:** Python 3.11+, FastAPI, pandas, openpyxl, xlrd, chardet | React 18, Vite, TypeScript

---

## What the User Can Test After This Phase

1. Open the app in a browser → see a file upload screen
2. Drag and drop (or click to select) a .csv, .xlsx, or .xls file
3. See the file's structure: file name, sheet names, row count, column names, column types, sample values, basic stats
4. Upload a second file → see both files' info
5. Try uploading an unsupported file → see an error message
6. Try uploading a file >5MB → see an error message

---

## File Structure

### Server

```
server/
├── requirements.txt
├── main.py                     # FastAPI app, CORS, routes
├── config.py                   # constants (MAX_FILE_SIZE, etc.)
├── models/
│   ├── api.py                  # Pydantic: UploadResponse, ErrorResponse
│   └── domain.py               # DataSource, ParsedFile, SheetData, SheetProfile, ColumnProfile
├── parsers/
│   ├── base.py                 # BaseParser ABC
│   ├── csv_parser.py           # CsvParser
│   ├── xlsx_parser.py          # XlsxParser
│   ├── xls_parser.py           # XlsParser
│   └── registry.py             # get_parser(filename) -> BaseParser
├── profiler/
│   └── profiler.py             # DataProfiler
└── session/
    ├── interface.py            # SessionStore ABC, SessionData
    └── memory_store.py         # MemorySessionStore
```

### Client

```
client/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── api.ts                  # uploadFiles()
    ├── types.ts                # TypeScript types matching API response
    ├── components/
    │   ├── upload/
    │   │   ├── UploadScreen.tsx
    │   │   └── FileDropzone.tsx
    │   └── session/
    │       ├── SessionScreen.tsx
    │       └── FileInfoBar.tsx
    └── styles/
        └── index.css
```

---

## Tasks

### Task 1: Server Project Setup

**Files:**
- Create: `server/requirements.txt`
- Create: `server/config.py`
- Create: `server/main.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-multipart==0.0.18
pandas==2.2.3
openpyxl==3.1.5
xlrd==2.0.1
chardet==5.2.0
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 2: Create config.py**

```python
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_SESSIONS = 50
SESSION_TTL_MINUTES = 30
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
```

- [ ] **Step 3: Create main.py with health check**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ChatBI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Install dependencies and verify server starts**

Run:
```bash
cd server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/api/health` — expect `{"status": "ok"}`.

- [ ] **Step 5: Commit**

```bash
git init
git add server/requirements.txt server/config.py server/main.py
git commit -m "feat: initialize FastAPI server with health check"
```

---

### Task 2: Domain Models

**Files:**
- Create: `server/models/__init__.py`
- Create: `server/models/domain.py`
- Create: `server/models/api.py`

- [ ] **Step 1: Create domain.py**

```python
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
```

- [ ] **Step 2: Create api.py**

```python
from pydantic import BaseModel


class FileInfo(BaseModel):
    name: str
    sheet_name: str
    rows: int
    columns: list[str]


class ColumnProfileResponse(BaseModel):
    name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    sample_values: list
    stats: dict | None


class SheetProfileResponse(BaseModel):
    file_name: str
    sheet_name: str
    row_count: int
    column_count: int
    columns: list[ColumnProfileResponse]


class UploadResponse(BaseModel):
    session_id: str
    files: list[FileInfo]
    profiles: list[SheetProfileResponse]
    warnings: list[str]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
```

- [ ] **Step 3: Create __init__.py**

```python
# models package
```

- [ ] **Step 4: Commit**

```bash
git add server/models/
git commit -m "feat: add domain and API models"
```

---

### Task 3: CSV Parser

**Files:**
- Create: `server/parsers/__init__.py`
- Create: `server/parsers/base.py`
- Create: `server/parsers/csv_parser.py`
- Create: `server/tests/__init__.py`
- Create: `server/tests/test_csv_parser.py`
- Create: `server/tests/fixtures/sample.csv`

- [ ] **Step 1: Create test fixture**

Create `server/tests/fixtures/sample.csv`:
```csv
date,product,amount,region
2024-01-15,Widget A,1200.50,North
2024-02-20,Widget B,850.00,South
2024-03-10,Widget A,1500.75,East
2024-04-05,Widget C,920.30,North
2024-05-18,Widget B,1100.00,West
```

- [ ] **Step 2: Create base parser**

Create `server/parsers/base.py`:
```python
from abc import ABC, abstractmethod
from io import BytesIO

from models.domain import ParsedFile


class BaseParser(ABC):
    @abstractmethod
    def parse(self, filename: str, content: BytesIO) -> ParsedFile:
        """Parse file content into a ParsedFile."""
        ...
```

- [ ] **Step 3: Write the failing test**

Create `server/tests/test_csv_parser.py`:
```python
from io import BytesIO
from pathlib import Path

import pytest

from parsers.csv_parser import CsvParser

FIXTURES = Path(__file__).parent / "fixtures"


def test_csv_parser_reads_file():
    content = (FIXTURES / "sample.csv").read_bytes()
    parser = CsvParser()
    result = parser.parse("sample.csv", BytesIO(content))

    assert result.name == "sample.csv"
    assert len(result.sheets) == 1
    assert result.sheets[0].name == "Sheet1"
    assert len(result.sheets[0].df) == 5
    assert list(result.sheets[0].df.columns) == ["date", "product", "amount", "region"]


def test_csv_parser_detects_semicolon_delimiter():
    csv_content = b"name;age;city\nAlice;30;NYC\nBob;25;LA"
    parser = CsvParser()
    result = parser.parse("semicolon.csv", BytesIO(csv_content))

    assert len(result.sheets[0].df) == 2
    assert list(result.sheets[0].df.columns) == ["name", "age", "city"]


def test_csv_parser_handles_empty_file():
    parser = CsvParser()
    with pytest.raises(ValueError, match="empty"):
        parser.parse("empty.csv", BytesIO(b""))
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd server && python -m pytest tests/test_csv_parser.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'parsers.csv_parser'`

- [ ] **Step 5: Implement CsvParser**

Create `server/parsers/csv_parser.py`:
```python
import csv
from io import BytesIO, StringIO

import chardet
import pandas as pd

from models.domain import ParsedFile, SheetData
from parsers.base import BaseParser


class CsvParser(BaseParser):
    def parse(self, filename: str, content: BytesIO) -> ParsedFile:
        raw = content.read()
        if not raw.strip():
            raise ValueError(f"File is empty: {filename}")

        encoding = chardet.detect(raw)["encoding"] or "utf-8"
        text = raw.decode(encoding)

        dialect = csv.Sniffer().sniff(text[:8192])
        df = pd.read_csv(StringIO(text), sep=dialect.delimiter)

        if df.empty:
            raise ValueError(f"File is empty: {filename}")

        sheet = SheetData(name="Sheet1", df=df)
        return ParsedFile(name=filename, sheets=[sheet])
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_csv_parser.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add server/parsers/ server/tests/
git commit -m "feat: add CSV parser with encoding and delimiter detection"
```

---

### Task 4: XLSX Parser

**Files:**
- Create: `server/parsers/xlsx_parser.py`
- Create: `server/tests/test_xlsx_parser.py`
- Create: `server/tests/fixtures/sample.xlsx` (generated in test)

- [ ] **Step 1: Write the failing test**

Create `server/tests/test_xlsx_parser.py`:
```python
from io import BytesIO

import pandas as pd
import pytest

from parsers.xlsx_parser import XlsxParser


def _make_xlsx(sheets: dict[str, pd.DataFrame]) -> BytesIO:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    buf.seek(0)
    return buf


def test_xlsx_single_sheet():
    df = pd.DataFrame({"product": ["A", "B"], "sales": [100, 200]})
    content = _make_xlsx({"Sheet1": df})
    parser = XlsxParser()
    result = parser.parse("test.xlsx", content)

    assert result.name == "test.xlsx"
    assert len(result.sheets) == 1
    assert result.sheets[0].name == "Sheet1"
    assert len(result.sheets[0].df) == 2
    assert list(result.sheets[0].df.columns) == ["product", "sales"]


def test_xlsx_multiple_sheets():
    sheets = {
        "Sales": pd.DataFrame({"month": ["Jan"], "revenue": [1000]}),
        "Inventory": pd.DataFrame({"item": ["Widget"], "stock": [50]}),
    }
    content = _make_xlsx(sheets)
    parser = XlsxParser()
    result = parser.parse("multi.xlsx", content)

    assert len(result.sheets) == 2
    assert result.sheets[0].name == "Sales"
    assert result.sheets[1].name == "Inventory"


def test_xlsx_empty_sheet_raises():
    df = pd.DataFrame()
    content = _make_xlsx({"Empty": df})
    parser = XlsxParser()
    with pytest.raises(ValueError, match="no data"):
        parser.parse("empty.xlsx", content)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd server && python -m pytest tests/test_xlsx_parser.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement XlsxParser**

Create `server/parsers/xlsx_parser.py`:
```python
from io import BytesIO

import pandas as pd

from models.domain import ParsedFile, SheetData
from parsers.base import BaseParser


class XlsxParser(BaseParser):
    def parse(self, filename: str, content: BytesIO) -> ParsedFile:
        xlsx = pd.ExcelFile(content, engine="openpyxl")
        sheets: list[SheetData] = []

        for sheet_name in xlsx.sheet_names:
            df = xlsx.parse(sheet_name)
            if not df.empty:
                sheets.append(SheetData(name=sheet_name, df=df))

        if not sheets:
            raise ValueError(f"File has no data: {filename}")

        return ParsedFile(name=filename, sheets=sheets)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_xlsx_parser.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add server/parsers/xlsx_parser.py server/tests/test_xlsx_parser.py
git commit -m "feat: add XLSX parser with multi-sheet support"
```

---

### Task 5: XLS Parser

**Files:**
- Create: `server/parsers/xls_parser.py`
- Create: `server/tests/test_xls_parser.py`

- [ ] **Step 1: Write the failing test**

Create `server/tests/test_xls_parser.py`:
```python
from io import BytesIO

import pandas as pd
import pytest

from parsers.xls_parser import XlsParser


def _make_xls(sheets: dict[str, pd.DataFrame]) -> BytesIO:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    buf.seek(0)
    # xlrd reads .xls but we test with .xlsx bytes that xlrd can also handle
    # In production, real .xls files use the old BIFF format
    return buf


def test_xls_parser_reads_file():
    df = pd.DataFrame({"name": ["Alice", "Bob"], "score": [95, 87]})
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)

    parser = XlsParser()
    result = parser.parse("test.xls", buf)

    assert result.name == "test.xls"
    assert len(result.sheets) >= 1
    assert len(result.sheets[0].df) == 2


def test_xls_parser_empty_raises():
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame().to_excel(writer, index=False)
    buf.seek(0)

    parser = XlsParser()
    with pytest.raises(ValueError, match="no data"):
        parser.parse("empty.xls", buf)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd server && python -m pytest tests/test_xls_parser.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement XlsParser**

Create `server/parsers/xls_parser.py`:
```python
from io import BytesIO

import pandas as pd

from models.domain import ParsedFile, SheetData
from parsers.base import BaseParser


class XlsParser(BaseParser):
    def parse(self, filename: str, content: BytesIO) -> ParsedFile:
        # Try xlrd first for true .xls files, fall back to openpyxl
        try:
            xls = pd.ExcelFile(content, engine="xlrd")
        except Exception:
            content.seek(0)
            xls = pd.ExcelFile(content, engine="openpyxl")

        sheets: list[SheetData] = []
        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name)
            if not df.empty:
                sheets.append(SheetData(name=sheet_name, df=df))

        if not sheets:
            raise ValueError(f"File has no data: {filename}")

        return ParsedFile(name=filename, sheets=sheets)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_xls_parser.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add server/parsers/xls_parser.py server/tests/test_xls_parser.py
git commit -m "feat: add XLS parser with xlrd/openpyxl fallback"
```

---

### Task 6: Parser Registry

**Files:**
- Create: `server/parsers/registry.py`
- Create: `server/tests/test_registry.py`

- [ ] **Step 1: Write the failing test**

Create `server/tests/test_registry.py`:
```python
import pytest

from parsers.registry import get_parser
from parsers.csv_parser import CsvParser
from parsers.xlsx_parser import XlsxParser
from parsers.xls_parser import XlsParser


def test_csv_extension():
    assert isinstance(get_parser("data.csv"), CsvParser)


def test_xlsx_extension():
    assert isinstance(get_parser("report.xlsx"), XlsxParser)


def test_xls_extension():
    assert isinstance(get_parser("old_report.xls"), XlsParser)


def test_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported"):
        get_parser("document.pdf")


def test_case_insensitive():
    assert isinstance(get_parser("DATA.CSV"), CsvParser)
    assert isinstance(get_parser("Report.XLSX"), XlsxParser)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd server && python -m pytest tests/test_registry.py -v`
Expected: FAIL

- [ ] **Step 3: Implement registry**

Create `server/parsers/registry.py`:
```python
from pathlib import Path

from parsers.base import BaseParser
from parsers.csv_parser import CsvParser
from parsers.xlsx_parser import XlsxParser
from parsers.xls_parser import XlsParser

_PARSERS: dict[str, type[BaseParser]] = {
    ".csv": CsvParser,
    ".xlsx": XlsxParser,
    ".xls": XlsParser,
}


def get_parser(filename: str) -> BaseParser:
    ext = Path(filename).suffix.lower()
    parser_class = _PARSERS.get(ext)
    if parser_class is None:
        raise ValueError(
            f"Unsupported file format: {ext}. "
            f"Supported formats: {', '.join(sorted(_PARSERS.keys()))}"
        )
    return parser_class()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_registry.py -v`
Expected: 5 passed

- [ ] **Step 5: Create parsers/__init__.py**

```python
# parsers package
```

- [ ] **Step 6: Commit**

```bash
git add server/parsers/
git commit -m "feat: add parser registry with extension-based dispatch"
```

---

### Task 7: Data Profiler

**Files:**
- Create: `server/profiler/__init__.py`
- Create: `server/profiler/profiler.py`
- Create: `server/tests/test_profiler.py`

- [ ] **Step 1: Write the failing test**

Create `server/tests/test_profiler.py`:
```python
import pandas as pd

from models.domain import DataSource, SheetData
from profiler.profiler import DataProfiler


def test_profile_numeric_column():
    df = pd.DataFrame({"sales": [100, 200, 300, 400, 500]})
    sheet = SheetData(name="Sheet1", df=df)
    source = DataSource(file_name="test.csv", sheet_name="Sheet1")
    profiler = DataProfiler()
    profile = profiler.profile(sheet, source)

    assert profile.row_count == 5
    assert profile.column_count == 1
    assert profile.source == source

    col = profile.columns[0]
    assert col.name == "sales"
    assert col.dtype == "numeric"
    assert col.null_count == 0
    assert col.null_pct == 0.0
    assert col.unique_count == 5
    assert col.stats["min"] == 100
    assert col.stats["max"] == 500
    assert col.stats["mean"] == 300.0


def test_profile_categorical_column():
    df = pd.DataFrame({"color": ["red", "blue", "red", "green", "blue"]})
    sheet = SheetData(name="Sheet1", df=df)
    source = DataSource(file_name="test.csv", sheet_name="Sheet1")
    profiler = DataProfiler()
    profile = profiler.profile(sheet, source)

    col = profile.columns[0]
    assert col.dtype == "categorical"
    assert col.unique_count == 3
    assert "top_values" in col.stats


def test_profile_datetime_column():
    df = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"])})
    sheet = SheetData(name="Sheet1", df=df)
    source = DataSource(file_name="test.csv", sheet_name="Sheet1")
    profiler = DataProfiler()
    profile = profiler.profile(sheet, source)

    col = profile.columns[0]
    assert col.dtype == "datetime"
    assert "min" in col.stats
    assert "max" in col.stats


def test_profile_with_nulls():
    df = pd.DataFrame({"value": [1.0, None, 3.0, None, 5.0]})
    sheet = SheetData(name="Sheet1", df=df)
    source = DataSource(file_name="test.csv", sheet_name="Sheet1")
    profiler = DataProfiler()
    profile = profiler.profile(sheet, source)

    col = profile.columns[0]
    assert col.null_count == 2
    assert col.null_pct == 40.0


def test_profile_sample_values():
    df = pd.DataFrame({"name": ["Alice", "Bob", "Carol", "Dave", "Eve"]})
    sheet = SheetData(name="Sheet1", df=df)
    source = DataSource(file_name="test.csv", sheet_name="Sheet1")
    profiler = DataProfiler()
    profile = profiler.profile(sheet, source)

    col = profile.columns[0]
    assert len(col.sample_values) <= 5
    assert all(isinstance(v, str) for v in col.sample_values)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd server && python -m pytest tests/test_profiler.py -v`
Expected: FAIL

- [ ] **Step 3: Implement DataProfiler**

Create `server/profiler/profiler.py`:
```python
import pandas as pd

from models.domain import ColumnProfile, DataSource, SheetData, SheetProfile


class DataProfiler:
    def profile(self, sheet: SheetData, source: DataSource) -> SheetProfile:
        df = sheet.df
        columns: list[ColumnProfile] = []

        for col_name in df.columns:
            series = df[col_name]
            dtype = self._infer_dtype(series)
            null_count = int(series.isna().sum())
            total = len(series)

            columns.append(
                ColumnProfile(
                    name=str(col_name),
                    dtype=dtype,
                    null_count=null_count,
                    null_pct=round(null_count / total * 100, 1) if total > 0 else 0.0,
                    unique_count=int(series.nunique()),
                    sample_values=self._get_sample_values(series),
                    stats=self._compute_stats(series, dtype),
                )
            )

        return SheetProfile(
            source=source,
            row_count=len(df),
            column_count=len(df.columns),
            columns=columns,
        )

    def _infer_dtype(self, series: pd.Series) -> str:
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            non_null = series.dropna()
            if len(non_null) > 0:
                try:
                    pd.to_datetime(non_null, format="mixed")
                    return "datetime"
                except (ValueError, TypeError):
                    pass
            if series.nunique() / max(len(series), 1) < 0.5:
                return "categorical"
            return "text"
        return "text"

    def _get_sample_values(self, series: pd.Series) -> list:
        non_null = series.dropna()
        samples = non_null.head(5).tolist()
        return [self._make_serializable(v) for v in samples]

    def _compute_stats(self, series: pd.Series, dtype: str) -> dict | None:
        non_null = series.dropna()
        if len(non_null) == 0:
            return None

        if dtype == "numeric":
            return {
                "min": self._make_serializable(non_null.min()),
                "max": self._make_serializable(non_null.max()),
                "mean": round(float(non_null.mean()), 2),
            }
        elif dtype == "datetime":
            return {
                "min": str(non_null.min()),
                "max": str(non_null.max()),
            }
        elif dtype == "categorical":
            top = non_null.value_counts().head(5)
            return {
                "top_values": [
                    {"value": str(v), "count": int(c)} for v, c in top.items()
                ]
            }
        return None

    def _make_serializable(self, value):
        if hasattr(value, "item"):
            return value.item()
        return value
```

- [ ] **Step 4: Create profiler/__init__.py**

```python
# profiler package
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_profiler.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add server/profiler/ server/tests/test_profiler.py
git commit -m "feat: add data profiler with type inference and stats"
```

---

### Task 8: Session Store

**Files:**
- Create: `server/session/__init__.py`
- Create: `server/session/interface.py`
- Create: `server/session/memory_store.py`
- Create: `server/tests/test_session_store.py`

- [ ] **Step 1: Write the failing test**

Create `server/tests/test_session_store.py`:
```python
import pytest

from session.memory_store import MemorySessionStore
from models.domain import SessionData


def _make_session_data() -> SessionData:
    return SessionData(files=[], profiles=[])


def test_create_and_get():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    data = _make_session_data()
    store.create("s1", data)
    result = store.get("s1")
    assert result is not None
    assert result.files == []


def test_get_nonexistent_returns_none():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    assert store.get("missing") is None


def test_get_updates_last_accessed():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    data = _make_session_data()
    store.create("s1", data)
    first_access = store.get("s1").last_accessed_at
    result = store.get("s1")
    assert result.last_accessed_at >= first_access


def test_delete():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    store.create("s1", _make_session_data())
    store.delete("s1")
    assert store.get("s1") is None


def test_capacity_limit():
    store = MemorySessionStore(max_sessions=2, ttl_minutes=30)
    store.create("s1", _make_session_data())
    store.create("s2", _make_session_data())
    with pytest.raises(RuntimeError, match="capacity"):
        store.create("s3", _make_session_data())


def test_session_count():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    store.create("s1", _make_session_data())
    store.create("s2", _make_session_data())
    assert store.session_count() == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd server && python -m pytest tests/test_session_store.py -v`
Expected: FAIL

- [ ] **Step 3: Create interface.py**

Create `server/session/interface.py`:
```python
from abc import ABC, abstractmethod

from models.domain import SessionData


class SessionStore(ABC):
    @abstractmethod
    def create(self, session_id: str, data: SessionData) -> None: ...

    @abstractmethod
    def get(self, session_id: str) -> SessionData | None: ...

    @abstractmethod
    def update(self, session_id: str, data: SessionData) -> None: ...

    @abstractmethod
    def delete(self, session_id: str) -> None: ...

    @abstractmethod
    def session_count(self) -> int: ...
```

- [ ] **Step 4: Implement MemorySessionStore**

Create `server/session/memory_store.py`:
```python
from datetime import datetime

from models.domain import SessionData
from session.interface import SessionStore


class MemorySessionStore(SessionStore):
    def __init__(self, max_sessions: int, ttl_minutes: int):
        self._store: dict[str, SessionData] = {}
        self._max_sessions = max_sessions
        self._ttl_minutes = ttl_minutes

    def create(self, session_id: str, data: SessionData) -> None:
        if len(self._store) >= self._max_sessions:
            raise RuntimeError("Server at capacity")
        self._store[session_id] = data

    def get(self, session_id: str) -> SessionData | None:
        data = self._store.get(session_id)
        if data is not None:
            data.last_accessed_at = datetime.now()
        return data

    def update(self, session_id: str, data: SessionData) -> None:
        if session_id not in self._store:
            return
        data.last_accessed_at = datetime.now()
        self._store[session_id] = data

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def session_count(self) -> int:
        return len(self._store)

    def cleanup_expired(self) -> int:
        now = datetime.now()
        expired = [
            sid
            for sid, data in self._store.items()
            if (now - data.last_accessed_at).total_seconds() > self._ttl_minutes * 60
        ]
        for sid in expired:
            del self._store[sid]
        return len(expired)
```

- [ ] **Step 5: Create session/__init__.py**

```python
# session package
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_session_store.py -v`
Expected: 6 passed

- [ ] **Step 7: Commit**

```bash
git add server/session/ server/tests/test_session_store.py
git commit -m "feat: add in-memory session store with capacity limits"
```

---

### Task 9: Upload API Endpoint

**Files:**
- Modify: `server/main.py`
- Create: `server/tests/test_upload_api.py`

- [ ] **Step 1: Write the failing test**

Create `server/tests/test_upload_api.py`:
```python
from io import BytesIO
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_upload_csv():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        content = (FIXTURES / "sample.csv").read_bytes()
        response = await client.post(
            "/api/upload",
            files={"files": ("sample.csv", content, "text/csv")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["files"]) == 1
    assert data["files"][0]["name"] == "sample.csv"
    assert data["files"][0]["rows"] == 5
    assert len(data["profiles"]) == 1


@pytest.mark.anyio
async def test_upload_unsupported_format():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/upload",
            files={"files": ("doc.pdf", b"fake content", "application/pdf")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_FORMAT"


@pytest.mark.anyio
async def test_upload_empty_file():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/upload",
            files={"files": ("empty.csv", b"", "text/csv")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_FILE"
```

Add `anyio` and `pytest-anyio` to requirements.txt:
```
anyio==4.7.0
pytest-anyio==0.0.0
```

Actually, use `httpx` with `pytest` directly. Update `server/requirements.txt` to add:
```
anyio==4.7.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd server && pip install anyio && python -m pytest tests/test_upload_api.py -v`
Expected: FAIL — endpoint doesn't exist yet

- [ ] **Step 3: Implement upload endpoint**

Update `server/main.py`:
```python
import uuid
from io import BytesIO

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import MAX_FILE_SIZE_BYTES, MAX_SESSIONS, SESSION_TTL_MINUTES, SUPPORTED_EXTENSIONS
from models.api import (
    ColumnProfileResponse,
    ErrorDetail,
    ErrorResponse,
    FileInfo,
    SheetProfileResponse,
    UploadResponse,
)
from models.domain import DataSource, ParsedFile, SessionData
from parsers.registry import get_parser
from profiler.profiler import DataProfiler
from session.memory_store import MemorySessionStore

app = FastAPI(title="ChatBI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_store = MemorySessionStore(max_sessions=MAX_SESSIONS, ttl_minutes=SESSION_TTL_MINUTES)
profiler = DataProfiler()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    # Check capacity
    if session_store.session_count() >= MAX_SESSIONS:
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(code="SERVICE_AT_CAPACITY", message="Server is busy. Please try again in a few minutes.")
            ).model_dump(),
        )

    parsed_files: list[ParsedFile] = []
    all_profiles = []
    file_infos: list[FileInfo] = []
    warnings: list[str] = []

    for upload_file in files:
        filename = upload_file.filename or "unknown"

        # Check extension
        try:
            parser = get_parser(filename)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="INVALID_FILE_FORMAT",
                        message=f"Unsupported format. Please upload .xlsx, .xls, or .csv files.",
                    )
                ).model_dump(),
            )

        # Read and check size
        content = await upload_file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error=ErrorDetail(code="FILE_TOO_LARGE", message="File exceeds 5MB limit.")
                ).model_dump(),
            )

        # Parse
        try:
            parsed = parser.parse(filename, BytesIO(content))
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error=ErrorDetail(code="EMPTY_FILE", message="This file appears to be empty.")
                ).model_dump(),
            )
        except Exception:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error=ErrorDetail(code="PARSE_ERROR", message="Could not read this file. It may be corrupted.")
                ).model_dump(),
            )

        parsed_files.append(parsed)

        # Profile each sheet
        for sheet in parsed.sheets:
            source = DataSource(file_name=filename, sheet_name=sheet.name)
            profile = profiler.profile(sheet, source)
            all_profiles.append(profile)

            file_infos.append(
                FileInfo(
                    name=filename,
                    sheet_name=sheet.name,
                    rows=profile.row_count,
                    columns=[c.name for c in profile.columns],
                )
            )

    # Create session
    session_id = str(uuid.uuid4())
    memory_bytes = sum(
        sheet.df.memory_usage(deep=True).sum()
        for pf in parsed_files
        for sheet in pf.sheets
    )
    session_data = SessionData(
        files=parsed_files,
        profiles=all_profiles,
        memory_bytes=int(memory_bytes),
    )
    session_store.create(session_id, session_data)

    # Build profile responses
    profile_responses = [
        SheetProfileResponse(
            file_name=p.source.file_name,
            sheet_name=p.source.sheet_name,
            row_count=p.row_count,
            column_count=p.column_count,
            columns=[
                ColumnProfileResponse(
                    name=c.name,
                    dtype=c.dtype,
                    null_count=c.null_count,
                    null_pct=c.null_pct,
                    unique_count=c.unique_count,
                    sample_values=c.sample_values,
                    stats=c.stats,
                )
                for c in p.columns
            ],
        )
        for p in all_profiles
    ]

    return UploadResponse(
        session_id=session_id,
        files=file_infos,
        profiles=profile_responses,
        warnings=warnings,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_upload_api.py -v`
Expected: 3 passed

- [ ] **Step 5: Run all server tests**

Run: `cd server && python -m pytest -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add server/main.py server/tests/test_upload_api.py server/requirements.txt
git commit -m "feat: add POST /api/upload endpoint with parsing and profiling"
```

---

### Task 10: Client Project Setup

**Files:**
- Create: `client/package.json`
- Create: `client/index.html`
- Create: `client/vite.config.ts`
- Create: `client/tsconfig.json`
- Create: `client/src/main.tsx`
- Create: `client/src/App.tsx`

- [ ] **Step 1: Initialize client project**

```bash
cd /Users/phuongthaoduong/Project/ChatBI
npm create vite@latest client -- --template react-ts
cd client
npm install
```

- [ ] **Step 2: Update vite.config.ts with API proxy**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **Step 3: Create minimal App.tsx**

Replace `client/src/App.tsx`:
```tsx
import { useState } from "react";

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  if (!sessionId) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
        <p>ChatBI — Upload screen coming next</p>
      </div>
    );
  }

  return <div>Session: {sessionId}</div>;
}

export default App;
```

- [ ] **Step 4: Verify client starts**

Run: `cd client && npm run dev`
Visit `http://localhost:5173` — expect to see "ChatBI — Upload screen coming next"

- [ ] **Step 5: Commit**

```bash
git add client/
git commit -m "feat: initialize React/Vite client with API proxy"
```

---

### Task 11: TypeScript Types & API Client

**Files:**
- Create: `client/src/types.ts`
- Create: `client/src/api.ts`

- [ ] **Step 1: Create types.ts**

```typescript
export interface FileInfo {
  name: string;
  sheet_name: string;
  rows: number;
  columns: string[];
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  null_count: number;
  null_pct: number;
  unique_count: number;
  sample_values: unknown[];
  stats: Record<string, unknown> | null;
}

export interface SheetProfile {
  file_name: string;
  sheet_name: string;
  row_count: number;
  column_count: number;
  columns: ColumnProfile[];
}

export interface UploadResponse {
  session_id: string;
  files: FileInfo[];
  profiles: SheetProfile[];
  warnings: string[];
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
  };
}
```

- [ ] **Step 2: Create api.ts**

```typescript
import { UploadResponse } from "./types";

const API_BASE = "/api";

export async function uploadFiles(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || "Upload failed");
  }

  return response.json();
}
```

- [ ] **Step 3: Commit**

```bash
git add client/src/types.ts client/src/api.ts
git commit -m "feat: add TypeScript types and API client for upload"
```

---

### Task 12: Upload Screen UI

**Files:**
- Create: `client/src/components/upload/UploadScreen.tsx`
- Create: `client/src/components/upload/FileDropzone.tsx`
- Modify: `client/src/App.tsx`

- [ ] **Step 1: Create FileDropzone component**

Create `client/src/components/upload/FileDropzone.tsx`:
```tsx
import { useCallback, useState, DragEvent, ChangeEvent } from "react";

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  isLoading: boolean;
  error: string | null;
}

export function FileDropzone({ onFilesSelected, isLoading, error }: FileDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) onFilesSelected(files);
    },
    [onFilesSelected]
  );

  const handleFileInput = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      if (files.length > 0) onFilesSelected(files);
    },
    [onFilesSelected]
  );

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      style={{
        border: `2px dashed ${isDragOver ? "#4f46e5" : "#d1d5db"}`,
        borderRadius: "12px",
        padding: "48px",
        textAlign: "center",
        cursor: isLoading ? "wait" : "pointer",
        backgroundColor: isDragOver ? "#eef2ff" : "#fafafa",
        transition: "all 0.2s",
      }}
    >
      {isLoading ? (
        <p>Uploading and analyzing...</p>
      ) : (
        <>
          <p style={{ fontSize: "18px", marginBottom: "8px" }}>
            Drop files here or click to upload
          </p>
          <p style={{ color: "#6b7280", fontSize: "14px" }}>
            Supports .csv, .xlsx, .xls (max 5MB)
          </p>
          <input
            type="file"
            multiple
            accept=".csv,.xlsx,.xls"
            onChange={handleFileInput}
            style={{ display: "none" }}
            id="file-input"
          />
          <label
            htmlFor="file-input"
            style={{
              display: "inline-block",
              marginTop: "16px",
              padding: "8px 24px",
              backgroundColor: "#4f46e5",
              color: "white",
              borderRadius: "6px",
              cursor: "pointer",
            }}
          >
            Choose Files
          </label>
        </>
      )}
      {error && (
        <p style={{ color: "#dc2626", marginTop: "12px" }}>{error}</p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create UploadScreen component**

Create `client/src/components/upload/UploadScreen.tsx`:
```tsx
import { useState } from "react";
import { uploadFiles } from "../../api";
import { UploadResponse } from "../../types";
import { FileDropzone } from "./FileDropzone";

interface UploadScreenProps {
  onUploadComplete: (data: UploadResponse) => void;
}

export function UploadScreen({ onUploadComplete }: UploadScreenProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFilesSelected = async (files: File[]) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await uploadFiles(files);
      onUploadComplete(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "24px",
      }}
    >
      <h1 style={{ fontSize: "32px", marginBottom: "8px" }}>ChatBI</h1>
      <p style={{ color: "#6b7280", marginBottom: "32px" }}>
        Upload your data files to get started
      </p>
      <div style={{ width: "100%", maxWidth: "500px" }}>
        <FileDropzone
          onFilesSelected={handleFilesSelected}
          isLoading={isLoading}
          error={error}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Update App.tsx**

Replace `client/src/App.tsx`:
```tsx
import { useState } from "react";
import { UploadResponse } from "./types";
import { UploadScreen } from "./components/upload/UploadScreen";

function App() {
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);

  if (!uploadData) {
    return <UploadScreen onUploadComplete={setUploadData} />;
  }

  return (
    <div style={{ padding: "24px" }}>
      <h2>Session: {uploadData.session_id}</h2>
      <pre>{JSON.stringify(uploadData, null, 2)}</pre>
    </div>
  );
}

export default App;
```

- [ ] **Step 4: Test end-to-end**

1. Start server: `cd server && uvicorn main:app --reload --port 8000`
2. Start client: `cd client && npm run dev`
3. Open `http://localhost:5173`
4. Upload `server/tests/fixtures/sample.csv`
5. Expect to see session ID and JSON profile data

- [ ] **Step 5: Commit**

```bash
git add client/src/
git commit -m "feat: add upload screen with drag-and-drop file upload"
```

---

### Task 13: File Info Display (SessionScreen + FileInfoBar)

**Files:**
- Create: `client/src/components/session/SessionScreen.tsx`
- Create: `client/src/components/session/FileInfoBar.tsx`
- Modify: `client/src/App.tsx`

- [ ] **Step 1: Create FileInfoBar component**

Create `client/src/components/session/FileInfoBar.tsx`:
```tsx
import { SheetProfile } from "../../types";

interface FileInfoBarProps {
  profiles: SheetProfile[];
  warnings: string[];
}

export function FileInfoBar({ profiles, warnings }: FileInfoBarProps) {
  return (
    <div style={{ borderBottom: "1px solid #e5e7eb", padding: "16px 24px" }}>
      <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
        {profiles.map((profile, i) => (
          <div
            key={i}
            style={{
              padding: "12px 16px",
              backgroundColor: "#f9fafb",
              borderRadius: "8px",
              border: "1px solid #e5e7eb",
            }}
          >
            <div style={{ fontWeight: 600, marginBottom: "4px" }}>
              {profile.file_name}
              {profile.sheet_name !== "Sheet1" && ` / ${profile.sheet_name}`}
            </div>
            <div style={{ fontSize: "14px", color: "#6b7280" }}>
              {profile.row_count.toLocaleString()} rows · {profile.column_count} columns
            </div>
            <div style={{ fontSize: "12px", color: "#9ca3af", marginTop: "4px" }}>
              {profile.columns.map((c) => c.name).join(", ")}
            </div>
          </div>
        ))}
      </div>
      {warnings.map((w, i) => (
        <div
          key={i}
          style={{
            marginTop: "8px",
            padding: "8px 12px",
            backgroundColor: "#fef3c7",
            borderRadius: "6px",
            fontSize: "14px",
            color: "#92400e",
          }}
        >
          {w}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create SessionScreen component**

Create `client/src/components/session/SessionScreen.tsx`:
```tsx
import { UploadResponse } from "../../types";
import { FileInfoBar } from "./FileInfoBar";

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
      <div style={{ padding: "24px", textAlign: "center", color: "#9ca3af" }}>
        Dashboard coming in Phase 2
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Update App.tsx to use SessionScreen**

Replace `client/src/App.tsx`:
```tsx
import { useState } from "react";
import { UploadResponse } from "./types";
import { UploadScreen } from "./components/upload/UploadScreen";
import { SessionScreen } from "./components/session/SessionScreen";

function App() {
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);

  if (!uploadData) {
    return <UploadScreen onUploadComplete={setUploadData} />;
  }

  return <SessionScreen data={uploadData} onReset={() => setUploadData(null)} />;
}

export default App;
```

- [ ] **Step 4: Test end-to-end**

1. Start server and client
2. Upload a file
3. Expect to see: file name, row count, column count, column names
4. Click "New Upload" → back to upload screen

- [ ] **Step 5: Commit**

```bash
git add client/src/
git commit -m "feat: add SessionScreen with FileInfoBar showing parsed file details"
```

---

## Phase 1 Completion Checklist

After completing all tasks, verify the full user flow:

- [ ] Open app → see upload screen with drop zone
- [ ] Upload a CSV → see file info (name, rows, columns, types)
- [ ] Upload an XLSX with multiple sheets → see each sheet listed
- [ ] Upload an unsupported file (.pdf) → see error message
- [ ] Upload a file >5MB → see error message
- [ ] Upload an empty file → see error message
- [ ] Click "New Upload" → return to upload screen
- [ ] All server tests pass: `cd server && python -m pytest -v`
