# Phase 4: Polish & Resilience — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the MVP production-ready — robust error handling, session cleanup, loading states, display caps, and UI polish.

**Architecture:** No new modules. This phase hardens existing code and fills in missing edge cases.

**Tech Stack:** Same as previous phases

**Depends on:** Phase 3 completed

---

## What the User Can Test After This Phase

1. Upload a large file → see warning about display cap, but charts reflect full data
2. Leave the app idle for 30+ minutes → session expires gracefully
3. See clear loading spinners during upload and chat
4. See user-friendly error messages for all failure modes
5. Multiple files with overlapping column names → correct results per dataset
6. Responsive layout that works on different screen sizes

---

## Tasks

### Task 1: Session Cleanup Background Task

**Files:**
- Modify: `server/main.py`
- Create: `server/tests/test_session_cleanup.py`

- [ ] **Step 1: Write the failing test**

Create `server/tests/test_session_cleanup.py`:
```python
from datetime import datetime, timedelta

import pytest

from models.domain import SessionData
from session.memory_store import MemorySessionStore


def _make_session(minutes_ago: int) -> SessionData:
    now = datetime.now()
    data = SessionData(files=[], profiles=[])
    data.last_accessed_at = now - timedelta(minutes=minutes_ago)
    return data


def test_cleanup_expired_sessions():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    store.create("fresh", _make_session(5))
    store.create("expired1", _make_session(35))
    store.create("expired2", _make_session(60))

    removed = store.cleanup_expired()

    assert removed == 2
    assert store.get("fresh") is not None
    assert store.get("expired1") is None
    assert store.get("expired2") is None


def test_cleanup_no_expired():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    store.create("s1", _make_session(5))
    store.create("s2", _make_session(10))

    removed = store.cleanup_expired()
    assert removed == 0
    assert store.session_count() == 2


def test_cleanup_frees_capacity():
    store = MemorySessionStore(max_sessions=2, ttl_minutes=30)
    store.create("old", _make_session(35))
    store.create("current", _make_session(5))

    # At capacity
    with pytest.raises(RuntimeError):
        store.create("new", _make_session(0))

    store.cleanup_expired()

    # Now has room
    store.create("new", _make_session(0))
    assert store.session_count() == 2
```

- [ ] **Step 2: Run tests to verify they pass**

The `cleanup_expired` method was already implemented in Phase 1. Run:
`cd server && python -m pytest tests/test_session_cleanup.py -v`
Expected: 3 passed

- [ ] **Step 3: Add background cleanup to main.py**

Add to `server/main.py`:
```python
import asyncio
import logging

from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


async def _cleanup_loop():
    while True:
        await asyncio.sleep(300)  # 5 minutes
        removed = session_store.cleanup_expired()
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired session(s). Active: {session_store.session_count()}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
```

Update the FastAPI app initialization:
```python
app = FastAPI(title="ChatBI", lifespan=lifespan)
```

- [ ] **Step 4: Commit**

```bash
git add server/main.py server/tests/test_session_cleanup.py
git commit -m "feat: add background session cleanup every 5 minutes"
```

---

### Task 2: Display Cap for Tabular Results

**Files:**
- Modify: `server/main.py`
- Modify: `server/models/api.py`
- Create: `server/tests/test_display_cap.py`

- [ ] **Step 1: Add display cap fields to API models**

Add to `server/models/api.py`:
```python
class ChatResponse(BaseModel):
    answer: str
    chart: ChartDataResponse | None = None
    total_rows: int | None = None
    displayed_rows: int | None = None
```

- [ ] **Step 2: Write the test**

Create `server/tests/test_display_cap.py`:
```python
from models.domain import ListResult, TabularResult

DISPLAY_CAP = 10_000


def test_tabular_result_within_cap():
    rows = [[i, f"item_{i}"] for i in range(100)]
    result = TabularResult(columns=["id", "name"], rows=rows)

    capped_rows = result.rows[:DISPLAY_CAP]
    assert len(capped_rows) == 100
    assert len(capped_rows) == len(result.rows)


def test_tabular_result_exceeds_cap():
    rows = [[i, f"item_{i}"] for i in range(15_000)]
    result = TabularResult(columns=["id", "name"], rows=rows)

    total = len(result.rows)
    capped_rows = result.rows[:DISPLAY_CAP]

    assert total == 15_000
    assert len(capped_rows) == DISPLAY_CAP


def test_list_result_not_capped():
    """List results (aggregations) are never capped — they're already summarized."""
    items = [{"label": f"item_{i}", "value": i} for i in range(50)]
    result = ListResult(items=items)
    assert len(result.items) == 50
```

- [ ] **Step 3: Run tests**

Run: `cd server && python -m pytest tests/test_display_cap.py -v`
Expected: 3 passed

- [ ] **Step 4: Apply display cap in chat endpoint**

In the chat endpoint in `server/main.py`, after executing the plan, add display cap logic:
```python
            total_rows = None
            displayed_rows = None

            if result.result_type == ResultType.TABULAR:
                total_rows = len(result.data.rows)
                if total_rows > 10_000:
                    displayed_rows = 10_000
                    result.data.rows = result.data.rows[:10_000]
```

Import `ResultType` at the top of main.py:
```python
from models.domain import ResultType
```

Update the ChatResponse return to include the counts:
```python
        return ChatResponse(
            answer=answer,
            chart=chart_response,
            total_rows=total_rows,
            displayed_rows=displayed_rows,
        )
```

- [ ] **Step 5: Commit**

```bash
git add server/main.py server/models/api.py server/tests/test_display_cap.py
git commit -m "feat: add 10K display cap for tabular results with row counts"
```

---

### Task 3: Comprehensive Error Handling on Server

**Files:**
- Modify: `server/main.py`

- [ ] **Step 1: Add global exception handler**

Add to `server/main.py`:
```python
from fastapi import Request
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=ErrorDetail(code="VALIDATION_ERROR", message="Invalid request. Please check your input.")
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(code="INTERNAL_ERROR", message="An unexpected error occurred. Please try again.")
        ).model_dump(),
    )
```

- [ ] **Step 2: Add file size check middleware**

Add to the upload endpoint, before parsing, a more descriptive size message:
```python
        if len(content) > MAX_FILE_SIZE_BYTES:
            size_mb = round(len(content) / (1024 * 1024), 1)
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="FILE_TOO_LARGE",
                        message=f"File '{filename}' is {size_mb}MB. Maximum allowed is 5MB.",
                    )
                ).model_dump(),
            )
```

- [ ] **Step 3: Add LLM retry with timeout**

In `server/llm/client.py`, update the LLMClient methods to use a timeout:
```python
    def __init__(self, timeout: int = 30):
        self._client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            timeout=timeout,
        )
```

- [ ] **Step 4: Commit**

```bash
git add server/main.py server/llm/client.py
git commit -m "feat: add global error handlers, size details, and LLM timeout"
```

---

### Task 4: Client Loading States & Error Display

**Files:**
- Modify: `client/src/components/upload/UploadScreen.tsx`
- Modify: `client/src/components/upload/FileDropzone.tsx`
- Modify: `client/src/components/session/SessionScreen.tsx`

- [ ] **Step 1: Add upload progress indicator to FileDropzone**

Update the loading state in `FileDropzone.tsx`:
```tsx
      {isLoading ? (
        <div>
          <div
            style={{
              width: "40px",
              height: "40px",
              border: "3px solid #e5e7eb",
              borderTopColor: "#4f46e5",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              margin: "0 auto 12px",
            }}
          />
          <p>Uploading and analyzing your data...</p>
          <p style={{ fontSize: "14px", color: "#6b7280" }}>
            This may take a few seconds
          </p>
        </div>
      ) : (
        /* existing content */
      )}
```

Add CSS keyframes to `client/src/styles/index.css`:
```css
@keyframes spin {
  to { transform: rotate(360deg); }
}
```

- [ ] **Step 2: Add session expired handling to SessionScreen**

Add to `SessionScreen.tsx`, a handler for session-expired errors during chat:
```tsx
  const handleSendMessage = async (question: string) => {
    /* ... existing code ... */
    try {
      const response = await askQuestion(data.session_id, question);
      /* ... */
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong.";
      if (message.includes("Session expired")) {
        // Force user back to upload screen
        onReset();
        return;
      }
      /* ... existing error handling ... */
    }
  };
```

- [ ] **Step 3: Add display cap warning to ChatMessage**

Update `ChatMessage.tsx` to show display cap info:
```tsx
interface ChatMessageProps {
  message: Message;
  totalRows?: number | null;
  displayedRows?: number | null;
}

export function ChatMessage({ message, totalRows, displayedRows }: ChatMessageProps) {
  /* ... existing rendering ... */
  {totalRows && displayedRows && totalRows > displayedRows && (
    <p style={{ fontSize: "12px", color: "#92400e", marginTop: "8px" }}>
      Showing {displayedRows.toLocaleString()} of {totalRows.toLocaleString()} matching rows.
      Charts and aggregations reflect the full dataset.
    </p>
  )}
}
```

- [ ] **Step 4: Commit**

```bash
git add client/src/
git commit -m "feat: add loading spinner, session expiry handling, and display cap warnings"
```

---

### Task 5: Multi-File Upload Validation

**Files:**
- Create: `server/tests/test_multi_file.py`
- Modify: `server/main.py` (if needed)

- [ ] **Step 1: Write multi-file tests**

Create `server/tests/test_multi_file.py`:
```python
from io import BytesIO

import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

from main import app


def _make_csv(data: dict) -> bytes:
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_upload_two_csv_files():
    sales_csv = _make_csv({"product": ["A", "B"], "sales": [100, 200]})
    inventory_csv = _make_csv({"product": ["A", "B"], "stock": [50, 30]})

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/upload",
            files=[
                ("files", ("sales.csv", sales_csv, "text/csv")),
                ("files", ("inventory.csv", inventory_csv, "text/csv")),
            ],
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) == 2
    assert len(data["profiles"]) == 2

    file_names = {f["name"] for f in data["files"]}
    assert "sales.csv" in file_names
    assert "inventory.csv" in file_names


@pytest.mark.anyio
async def test_upload_mixed_valid_invalid():
    """If one file is invalid, the entire upload fails."""
    sales_csv = _make_csv({"product": ["A"], "sales": [100]})

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/upload",
            files=[
                ("files", ("sales.csv", sales_csv, "text/csv")),
                ("files", ("doc.pdf", b"fake", "application/pdf")),
            ],
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_FORMAT"


@pytest.mark.anyio
async def test_profiles_have_correct_source():
    sales_csv = _make_csv({"month": ["Jan"], "revenue": [1000]})
    costs_csv = _make_csv({"month": ["Jan"], "cost": [500]})

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/upload",
            files=[
                ("files", ("sales.csv", sales_csv, "text/csv")),
                ("files", ("costs.csv", costs_csv, "text/csv")),
            ],
        )

    data = response.json()
    profiles = data["profiles"]

    sales_profile = next(p for p in profiles if p["file_name"] == "sales.csv")
    costs_profile = next(p for p in profiles if p["file_name"] == "costs.csv")

    assert "revenue" in [c["name"] for c in sales_profile["columns"]]
    assert "cost" in [c["name"] for c in costs_profile["columns"]]
```

- [ ] **Step 2: Run tests**

Run: `cd server && python -m pytest tests/test_multi_file.py -v`
Expected: 3 passed

- [ ] **Step 3: Commit**

```bash
git add server/tests/test_multi_file.py
git commit -m "test: add multi-file upload validation tests"
```

---

### Task 6: Responsive Layout & UI Polish

**Files:**
- Modify: `client/src/styles/index.css`
- Modify: `client/src/components/session/DashboardView.tsx`
- Modify: `client/src/components/upload/UploadScreen.tsx`

- [ ] **Step 1: Update global styles**

Replace `client/src/styles/index.css`:
```css
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: #111827;
  background-color: #ffffff;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive chart grid */
@media (max-width: 768px) {
  .chart-grid {
    grid-template-columns: 1fr !important;
  }

  .insight-row {
    flex-direction: column !important;
  }
}
```

- [ ] **Step 2: Add CSS class names to DashboardView**

Update `client/src/components/session/DashboardView.tsx` grid:
```tsx
      <div
        className="chart-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
          gap: "16px",
        }}
      >
```

Update insights row:
```tsx
      {insights.length > 0 && (
        <div
          className="insight-row"
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap",
            marginBottom: "24px",
          }}
        >
```

- [ ] **Step 3: Add max-width constraint to upload screen**

In `UploadScreen.tsx`, ensure the dropzone is centered and constrained:
```tsx
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "24px",
        maxWidth: "600px",
        margin: "0 auto",
      }}
    >
```

- [ ] **Step 4: Test on narrow viewport**

1. Open browser DevTools → toggle device toolbar
2. Set viewport to 375px (mobile)
3. Charts should stack vertically
4. Chat input should remain usable

- [ ] **Step 5: Commit**

```bash
git add client/src/
git commit -m "feat: add responsive layout and UI polish"
```

---

### Task 7: Final Integration Test

**Files:**
- No new files — manual testing

- [ ] **Step 1: Full happy path test**

1. Start server: `cd server && DEEPSEEK_API_KEY=your_key uvicorn main:app --reload --port 8000`
2. Start client: `cd client && npm run dev`
3. Open `http://localhost:5173`
4. Upload `server/tests/fixtures/sample.csv`
5. Verify: dashboard with charts + insights appear
6. Ask: "Which product had the highest sales?" → verify answer with chart
7. Ask: "What does this chart mean?" → verify text-only answer
8. Ask: "Show me sales by region" → verify new chart
9. Toggle between dashboard and chat views
10. Click "New Upload" → upload a different file → verify new dashboard

- [ ] **Step 2: Error path test**

1. Upload a .pdf file → verify error message
2. Upload an empty .csv → verify error message
3. Wait for session to expire (or manually clear) → ask question → verify "session expired" redirect
4. Stop the server → try to upload → verify "connection lost" message

- [ ] **Step 3: Run all server tests**

Run: `cd server && python -m pytest -v`
Expected: All tests pass

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete ChatBI MVP — Phase 4 polish and resilience"
```

---

## Phase 4 Completion Checklist

- [ ] Session cleanup runs automatically (check server logs)
- [ ] Large result sets show display cap warning
- [ ] Loading spinner during upload
- [ ] "Thinking..." indicator during chat
- [ ] Error messages are user-friendly for all failure modes
- [ ] Session expiry redirects to upload screen
- [ ] Multiple files upload correctly with distinct profiles
- [ ] Layout is responsive on mobile viewports
- [ ] All server tests pass
- [ ] Full happy path works end-to-end

---

## MVP Complete

After Phase 4, the ChatBI MVP is feature-complete:

- Upload CSV/Excel files
- Auto-generated dashboard with charts and insights
- Chat with your data — computational and conversational questions
- Robust error handling and session management
- Clean, responsive UI
