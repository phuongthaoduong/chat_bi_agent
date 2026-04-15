# ChatBI — Architecture Design Spec

> **Date:** 2026-04-15
> **Status:** Approved
> **Audience:** Engineering

---

## 1. Overview

ChatBI is a web application that lets users upload data files (Excel, CSV), automatically generates a dashboard with charts and insights, and allows follow-up questions via natural language chat.

**Core flow:** Upload files → Auto-generated dashboard → Chat with your data.

**Target users:** General audience, designed with small business personas in mind — owners, warehouse managers, finance staff who need quick answers from their data without technical skills.

### MVP Constraints

- No authentication
- No persistence — sessions are ephemeral (architecture supports adding persistence later)
- Session lifecycle: 30-minute inactivity TTL, max 50 concurrent sessions
- Single-worker deployment (multi-worker requires shared session store)
- File size limit: 5MB per file
- All analysis runs on full dataset; tabular API responses capped at 10K rows for display only
- Supported formats: .xlsx, .xls, .csv only

---

## 2. Architecture

Monolith-first approach: React/Vite SPA client + Python FastAPI server + DeepSeek API.

```
┌─────────────────────────────────┐
│        Client (React/Vite)      │
│                                 │
│  ┌───────────┐  ┌────────────┐  │
│  │ Upload UI │  │ Chat View  │  │
│  └─────┬─────┘  └─────┬──────┘  │
│        │               │        │
│  ┌─────▼───────────────▼─────┐  │
│  │  Dashboard / Charts       │  │
│  │  (ECharts)                │  │
│  └───────────┬───────────────┘  │
└──────────────┼──────────────────┘
               │ HTTP
┌──────────────▼──────────────────┐
│       Server (FastAPI)          │
│                                 │
│  ┌──────────┐  ┌─────────────┐  │
│  │  File    │  │   Chat /    │  │
│  │  Parser  │  │   Query     │  │
│  │  Module  │  │   Engine    │  │
│  └────┬─────┘  └──────┬──────┘  │
│       │               │        │
│  ┌────▼────┐  ┌───────▼──────┐  │
│  │Profiler │  │  Analysis    │  │
│  │         │  │  Engine      │  │
│  └─────────┘  └───────┬──────┘  │
│                       │        │
│              ┌────────▼───────┐  │
│              │ DeepSeek Client│  │
│              └────────────────┘  │
└─────────────────────────────────┘
```

**Why monolith:** For MVP constraints (small files, no auth, ephemeral sessions), a monolith is the simplest to build, deploy, and debug. FastAPI's async support handles concurrent LLM calls. Services can be extracted later if a specific bottleneck appears.

---

## 3. Data Flow

### Flow 1: File Upload → Auto Dashboard

```
User drops file(s)
  → Client sends file(s) via POST /api/upload (multipart)
  → Server: File Parser detects format, extracts DataFrame(s)
  → Server: DataProfiler generates SheetProfile per sheet
  → Server: LLMClient.suggest_dashboard() sends profiles to DeepSeek
  → DeepSeek returns structured AnalysisPlans + text insights
  → Server: AnalysisEngine.execute_plan() runs each plan
  → Server returns: session_id, file info, insights, chart data
  → Client renders dashboard with charts + insight cards
```

### Flow 2: Chat Follow-up Question (Classify → Compute → Narrate)

The chat flow first classifies the question, then branches into two paths. The LLM never generates answer text about data before real computation has occurred.

```
User asks a question
  → Client sends POST /api/chat { session_id, question }
  → Server: Loads session data from session store
  → LLM Call 1: LLMClient.interpret_question() sends question + profiles + history
      → DeepSeek classifies question and returns QuestionInterpretation:
          - question_type: COMPUTATIONAL or CONVERSATIONAL
          - plan: AnalysisPlan (if COMPUTATIONAL) or null (if CONVERSATIONAL)

  COMPUTATIONAL path (two LLM calls total):
    → Server: AnalysisEngine.execute_plan() runs the plan on full dataset
        → Produces concrete AnalysisResult with real numbers
    → LLM Call 2: LLMClient.format_answer(question, plan, result)
        → DeepSeek narrates the actual computed values
    → Server returns: answer text + chart data

  CONVERSATIONAL path (one LLM call total):
    → LLM already has profiles + chat history (including prior computed results)
    → LLM Call 2: LLMClient.format_answer(question, plan=null, result=null)
        → DeepSeek provides interpretive answer based on context
    → Server returns: answer text, chart = null
```

**Question classification examples:**

| Question | Type | Behavior |
|---|---|---|
| "What was total revenue in March?" | COMPUTATIONAL | Plan → execute → narrate real numbers |
| "Which product sold the most?" | COMPUTATIONAL | Plan → execute → narrate real numbers |
| "What does this chart tell us?" | CONVERSATIONAL | Interpret using profile + chat history |
| "Summarize the overall trend" | CONVERSATIONAL | Narrate based on profile stats + prior results |
| "Why might sales be declining?" | CONVERSATIONAL | Interpretive analysis, no computation |

**Why two LLM calls for computational questions:** If the LLM generates the answer before computation, it can only guess based on schema and sample values — leading to hallucinated numbers. By computing first and narrating second, every number in the answer is grounded in real data. The cost of an extra API call is negligible compared to the cost of wrong answers for business users making decisions.

**Why single call is safe for conversational questions:** These questions don't require specific numbers from the data. The LLM interprets patterns, explains charts, or provides business context. The profile stats and prior computed results in chat history give it sufficient grounding. The prompt explicitly instructs the LLM to distinguish interpretation from fact.

**Key decisions:**
- Session data stays in memory (dict of session_id → SessionData). Simple, fast, no database. Data lost on restart — acceptable for ephemeral MVP.
- LLM never generates executable code. It produces structured analysis plans.
- LLM never generates answer text containing data-dependent numbers without seeing real computed results first.
- Conversational answers are grounded in profile stats and prior chat results, not hallucinated.
- DeepSeek receives SheetProfile (schema + stats + sample values) as context, never the full dataset.

---

## 4. API Design

Three endpoints for MVP.

### `POST /api/upload`

**Input:** Multipart file upload (one or multiple files)

**Response:**
```json
{
  "session_id": "abc123",
  "files": [
    { "name": "sales.xlsx", "rows": 1200, "columns": ["date", "product", "amount"] }
  ],
  "warnings": [],
  "summary": { "total_rows": 1200, "column_types": {} },
  "insights": ["Total revenue is $45K", "March had the highest sales"],
  "charts": [
    { "type": "bar", "title": "Monthly Sales", "data": {}, "options": {} }
  ]
}
```

### `POST /api/chat`

**Input:**
```json
{
  "session_id": "abc123",
  "question": "Which product had the highest sales in March?"
}
```

**Response:**
```json
{
  "answer": "Product X had the highest sales in March with $12,300.",
  "chart": { "type": "bar", "title": "Top Products - March", "data": {} }
}
```

`chart` is `null` when the answer doesn't warrant a visualization.

### `GET /api/session/{session_id}`

Retrieve current session state (file info, previous charts). Useful if client needs to re-render after a page refresh during the same session. Same response structure as the upload response.

**Design notes:**
- No auth headers for MVP
- Session ID is a UUID generated server-side
- File size limit enforced at 5MB per file via FastAPI middleware
- All error responses follow a consistent `{ error: { code, message } }` envelope

---

## 5. File Parser Module

Two separate layers: **Parsing** (read bytes → DataFrame) and **Profiling** (understand the data).

### Supported Formats

| Format | Library | Notes |
|---|---|---|
| `.xlsx` | `openpyxl` | Modern Excel |
| `.xls` | `xlrd` | Legacy Excel (separate handler) |
| `.csv` | `pandas` (built-in) | Auto-detect delimiter and encoding via `chardet` |

PDF and Google Sheets deferred to post-MVP.

### Parsing Layer

```python
class FileParser:
    def parse(file: UploadFile) -> ParsedFile  # 1:1 mapping

class ParsedFile:
    name: str
    sheets: list[SheetData]  # CSV always has 1 sheet

class SheetData:
    name: str
    df: pd.DataFrame
```

Format resolved by file extension → dispatched via parser registry.

```python
class BaseParser(ABC):
    @abstractmethod
    def parse(file: UploadFile) -> ParsedFile

class XlsxParser(BaseParser): ...  # openpyxl
class XlsParser(BaseParser): ...   # xlrd
class CsvParser(BaseParser): ...   # pandas + chardet
```

### Profiling Layer

```python
class DataProfiler:
    def profile(sheet: SheetData) -> SheetProfile

class SheetProfile:
    source: DataSource      # identifies which file/sheet this profile belongs to
    row_count: int
    column_count: int
    columns: list[ColumnProfile]

class ColumnProfile:
    name: str
    dtype: str          # "numeric", "categorical", "datetime", "text"
    null_count: int
    null_pct: float
    unique_count: int
    sample_values: list  # 3-5 example values for LLM context
    stats: dict | None   # min/max/mean for numeric, top values for categorical
```

### Data Completeness Guarantee

All rows are parsed and profiled — no truncation at the parsing or profiling layer. The full DataFrame is stored in the session and used for all analysis computations.

A **display cap** of 10K rows applies only when the API serializes tabular results (e.g., a filtered list of rows). This is enforced in the route handlers, not in the parser or analysis engine. When the cap applies, the response includes:
- `"total_rows": 45000` — the true count
- `"displayed_rows": 10000` — what's in the response
- A warning: `"Showing 10,000 of 45,000 matching rows. Charts and aggregations reflect the full dataset."`

Charts and aggregated metrics always reflect the complete dataset.

### Not in MVP
- No PDF or Google Sheets parsing
- No cross-file joins
- No data transformation or cleaning (that's the analysis layer's job)

---

## 6. Data Analysis & LLM Integration

### Core Principle: Structured Plans, Not Code

The LLM never generates executable code. It produces a structured JSON plan describing *what* to compute. The Analysis Engine interprets and executes the plan using a fixed set of operations.

### Analysis Plan Schema

```python
class DataSource:
    file_name: str
    sheet_name: str

class AnalysisPlan:
    source: DataSource              # which dataset to query
    intent: AnalysisIntent
    target_fields: list[str]
    group_by: list[str] | None
    filters: list[FilterCondition] | None
    sort: SortSpec | None
    limit: int | None
    chart: ChartSpec | None

class AnalysisIntent(Enum):
    AGGREGATE = "aggregate"
    DISTRIBUTION = "distribution"
    TREND = "trend"
    COMPARISON = "comparison"
    TOP_N = "top_n"
    CORRELATION = "correlation"

class FilterCondition:
    field: str
    operator: str    # "eq", "ne", "gt", "lt", "gte", "lte", "in", "contains"
    value: Any

class SortSpec:
    field: str
    direction: str   # "asc", "desc"

class ChartSpec:
    chart_type: str  # "bar", "line", "pie", "scatter"
    title: str
    x_axis: str | None
    y_axis: str | None
```

### Analysis Engine

```python
class AnalysisEngine:
    def execute_plan(plan: AnalysisPlan,
                     sheets: list[SheetData]) -> AnalysisResult
    def generate_overview(profiles: list[SheetProfile],
                          plans: list[AnalysisPlan],
                          sheets: list[SheetData]) -> OverviewResult

class AnalysisResult:
    result_type: ResultType
    data: TabularResult | ScalarResult | ListResult
    chart_data: ChartData | None

class ResultType(Enum):
    TABULAR = "tabular"
    SCALAR = "scalar"
    LIST = "list"

class TabularResult:
    columns: list[str]
    rows: list[list[Any]]

class ScalarResult:
    label: str
    value: Any

class ListResult:
    items: list[dict]  # [{"label": "Product A", "value": 1200}, ...]
```

The engine validates every plan before execution:
1. **Source validation** — checks that `plan.source` (file_name + sheet_name) exists in the session
2. **Column validation** — checks that all referenced columns exist in the specified dataset
3. **Operator/type validation** — checks that operators are valid and types are compatible

Invalid plans return a clear error at the validation step, before any computation.

### LLM Client (Classify → Compute → Narrate)

```python
class QuestionType(Enum):
    COMPUTATIONAL = "computational"     # needs data query
    CONVERSATIONAL = "conversational"   # interpretive, no computation needed

class QuestionInterpretation:
    question_type: QuestionType
    plan: AnalysisPlan | None           # null for conversational questions

class LLMClient:
    # Dashboard: single call (insights are profile-level, acceptable)
    def suggest_dashboard(profiles: list[SheetProfile]) -> DashboardSuggestion

    # Chat: Call 1 — classify question and produce plan if computational
    def interpret_question(question: str,
                           profiles: list[SheetProfile],
                           chat_history: list[Message]) -> QuestionInterpretation

    # Chat: Call 2 — narrate computed result (computational)
    #                or provide interpretive answer (conversational)
    def format_answer(question: str,
                      plan: AnalysisPlan | None,
                      result: AnalysisResult | None,
                      profiles: list[SheetProfile],
                      chat_history: list[Message]) -> str

class DashboardSuggestion:
    insights: list[str]
    plans: list[AnalysisPlan]
```

**`format_answer` handles both paths:**
- **Computational:** receives `plan` + `result` with real data → narrates facts
- **Conversational:** receives `plan=None`, `result=None` → interprets using profiles + chat history context

**Dashboard insights** are derived from profile-level stats (totals, averages, column distributions) which the profiler computes over the full dataset. These are acceptable because the profiler has already seen all the data — the LLM is narrating real stats, not guessing.

### Prompt Design

Prompts enforce strict JSON output with explicit schema constraints.

**Dashboard prompt:**
```
You are a data analyst. Given the dataset schemas below, suggest 3-5
charts that give a business user the most useful overview.

AVAILABLE DATASETS:
{dataset_inventory_json}
// Example:
// - "sales.xlsx" / "Sheet1": columns [date, product, amount, region] (1200 rows)
// - "inventory.csv" / "Sheet1": columns [product, stock, warehouse] (500 rows)

Respond with EXACTLY this JSON structure:
{
  "insights": ["string"],
  "plans": [
    {
      "source": { "file_name": "sales.xlsx", "sheet_name": "Sheet1" },
      "intent": "aggregate|distribution|trend|comparison|top_n|correlation",
      "target_fields": ["column_name"],
      "group_by": ["column_name"] or null,
      "filters": [...] or null,
      "sort": {"field": "...", "direction": "asc|desc"} or null,
      "limit": number or null,
      "chart": {
        "chart_type": "bar|line|pie|scatter",
        "title": "string",
        "x_axis": "column_name" or null,
        "y_axis": "column_name" or null
      }
    }
  ]
}

RULES:
- Every plan MUST include a "source" specifying which dataset to query
- Only reference columns that exist in the specified dataset's schema
- Only use intents from the allowed list
- Keep insights concise (1 sentence each)
- Suggest charts that highlight different aspects of the data
```

**Chat prompt (Call 1 — classify and interpret):**
```
You are a data analyst. Given the dataset schemas and the user's question,
first classify the question, then produce an analysis plan if needed.

AVAILABLE DATASETS:
{dataset_inventory_json}

CHAT HISTORY:
{chat_history_json}

USER QUESTION:
{question}

Respond with EXACTLY this JSON structure:
{
  "question_type": "computational" or "conversational",
  "plan": {
    "source": { "file_name": "...", "sheet_name": "..." },
    "intent": "aggregate|distribution|trend|comparison|top_n|correlation",
    "target_fields": ["column_name"],
    "group_by": ["column_name"] or null,
    "filters": [{"field": "...", "operator": "eq|gt|lt|...", "value": "..."}] or null,
    "sort": {"field": "...", "direction": "asc|desc"} or null,
    "limit": number or null,
    "chart": { ... } or null
  } or null
}

RULES:
- Classify as "computational" if the question requires querying data
  (aggregations, filtering, ranking, comparisons, trends)
- Classify as "conversational" if the question is interpretive
  (explaining charts, summarizing patterns, asking "why", general advice)
- If "computational", plan MUST include a "source" and valid column references
- If "conversational", set plan to null
- Do NOT include any answer text
```

**Chat prompt (Call 2 — format answer, computational path):**
```
You are a data analyst assistant. The user asked a question and
the system has computed the result. Write a clear, concise answer
based on the actual data provided.

USER QUESTION:
{question}

COMPUTED RESULT:
{analysis_result_json}

RULES:
- Only state facts that appear in the computed result
- Do not invent or estimate numbers
- Keep the answer to 1-3 sentences
- Use natural language appropriate for a non-technical business user
```

**Chat prompt (Call 2 — format answer, conversational path):**
```
You are a data analyst assistant. The user asked an interpretive question.
Answer based on the dataset context and conversation history provided.

AVAILABLE DATASETS:
{dataset_inventory_json}

RECENT CHAT HISTORY (including prior computed results):
{chat_history_with_results_json}

USER QUESTION:
{question}

RULES:
- Base your answer on the dataset profile and prior computed results in chat history
- Do not invent specific numbers unless they appear in the provided context
- Clearly distinguish interpretation from established fact
- Keep the answer to 2-4 sentences
- Use natural language appropriate for a non-technical business user
```

All prompts include a dataset inventory with fully qualified identifiers (file_name / sheet_name), column names, types, sample values, and summary stats.

---

## 7. Client Architecture

### Page Layout

Single-page app with three states:

```
State 1: Landing          State 2: Dashboard           State 3: Chat Focus
┌──────────────────┐    ┌──────────────────────────┐  ┌──────────────────────────┐
│                  │    │  File Info Bar            │  │  File Info Bar            │
│                  │    ├──────────────────────────┤  ├──────────────────────────┤
│   Drop files     │    │  Insight Cards           │  │                          │
│   here or        │    │  ┌─────┐ ┌─────┐ ┌─────┐│  │  Chart Result            │
│   click to       │    │  │stat │ │stat │ │stat ││  │                          │
│   upload         │    │  └─────┘ └─────┘ └─────┘│  ├──────────────────────────┤
│                  │    ├──────────────────────────┤  │                          │
│                  │    │  Charts Grid             │  │  Chat History            │
│                  │    │  ┌──────────┐┌──────────┐│  │  - Q: ...                │
│                  │    │  │  chart   ││  chart   ││  │  - A: ...                │
│                  │    │  └──────────┘└──────────┘│  │                          │
│                  │    │  ┌──────────┐┌──────────┐│  ├──────────────────────────┤
│                  │    │  │  chart   ││  chart   ││  │  ┌────────────────┐ Send │
│                  │    │  └──────────┘└──────────┘│  │  │  Ask question  │  →   │
└──────────────────┘    ├──────────────────────────┤  │  └────────────────┘      │
                        │  ┌────────────────┐ Send │  └──────────────────────────┘
                        │  │  Ask question  │  →   │
                        │  └────────────────┘      │
                        └──────────────────────────┘
```

- State 1 → 2: After successful upload
- State 2 → 3: When user starts chatting
- User can toggle back to full dashboard view

### Component Tree

```
App
├── UploadScreen
│   └── FileDropzone
└── SessionScreen              # owns all session state
    ├── FileInfoBar
    ├── ViewToggle             # switch dashboard / chat
    ├── DashboardView          # child view
    │   ├── InsightCard(s)
    │   ├── ChartCard(s)
    │   │   └── Chart          # ECharts wrapper
    │   └── ChatInput
    └── ChatView               # child view
        ├── ChartDisplay
        ├── ChatMessage(s)
        └── ChatInput
```

Shared components (Chart, ChartCard, InsightCard, ChatMessage, ChatInput) live in `components/shared/`.

### Charting: ECharts (via `echarts-for-react`)

Chosen for: rich chart types, large dataset support, interactive features (tooltips, zoom), strong documentation.

### State Management

Simple React state at SessionScreen level — no Redux or external library.

```
useState / useReducer:
  - sessionId: string | null
  - files: FileInfo[]
  - insights: string[]
  - charts: ChartData[]
  - chatHistory: Message[]
  - isLoading: boolean
  - warnings: string[]
```

### API Client

Single `api.ts` with three functions using `fetch`:

```typescript
async function uploadFiles(files: File[]): Promise<UploadResponse>
async function askQuestion(sessionId: string, question: string): Promise<ChatResponse>
async function getSession(sessionId: string): Promise<SessionResponse>
```

---

## 8. Project Structure

```
ChatBI/
├── client/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api.ts
│       ├── types.ts
│       ├── components/
│       │   ├── upload/
│       │   │   ├── UploadScreen.tsx
│       │   │   └── FileDropzone.tsx
│       │   ├── session/
│       │   │   ├── SessionScreen.tsx
│       │   │   ├── FileInfoBar.tsx
│       │   │   ├── DashboardView.tsx
│       │   │   ├── ChatView.tsx
│       │   │   └── ViewToggle.tsx
│       │   └── shared/
│       │       ├── Chart.tsx
│       │       ├── ChartCard.tsx
│       │       ├── InsightCard.tsx
│       │       ├── ChatMessage.tsx
│       │       └── ChatInput.tsx
│       └── styles/
│           └── index.css
│
├── server/
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── api.py              # Pydantic: request/response ONLY
│   │   └── domain.py           # domain types ONLY
│   ├── parsers/
│   │   ├── base.py
│   │   ├── csv_parser.py
│   │   ├── xlsx_parser.py
│   │   ├── xls_parser.py
│   │   └── registry.py
│   ├── profiler/
│   │   └── profiler.py
│   ├── analysis/
│   │   └── engine.py
│   ├── llm/
│   │   ├── client.py
│   │   └── prompts.py
│   └── session/
│       ├── interface.py        # SessionStore ABC
│       └── memory_store.py     # in-memory implementation
│
├── .docs/
│   └── .architectture_design/
├── competitor_analysis.md
└── painpoint.md
```

### Boundary Rules

- `models/api.py` defines what goes over the wire. `models/domain.py` defines internal types. They never import each other.
- Conversion between API and domain types happens in `main.py` (route handlers) — the only place where both are imported.
- Only route handlers interact with the session store. Parsers, profiler, analysis engine, and LLM client receive data as function arguments.
- Swapping session storage later means implementing a new `SessionStore` subclass — nothing else changes.

### Session Lifecycle Management

The in-memory session store has explicit bounds to prevent unbounded memory growth.

```python
class SessionStore(ABC):
    def create(session_id: str, data: SessionData) -> None
    def get(session_id: str) -> SessionData | None
    def update(session_id: str, data: SessionData) -> None
    def delete(session_id: str) -> None

class SessionData:
    files: list[ParsedFile]
    profiles: list[SheetProfile]
    chat_history: list[Message]
    created_at: datetime
    last_accessed_at: datetime
    memory_bytes: int              # approximate DataFrame memory footprint
```

**Lifecycle rules:**
- **TTL:** Sessions expire after 30 minutes of inactivity (`last_accessed_at` + 30min). Every `get()` call updates `last_accessed_at`.
- **Cleanup:** A background task runs every 5 minutes to evict expired sessions and free memory.
- **Capacity cap:** Maximum 50 concurrent sessions. When the cap is hit, new uploads return a `503 SERVICE_AT_CAPACITY` error with message: "Server is busy. Please try again in a few minutes."
- **Memory tracking:** Each session tracks `memory_bytes` (sum of `df.memory_usage(deep=True)` for all DataFrames). Logged for observability.
- **Single-worker scope:** This design assumes a single FastAPI worker process. Multi-worker deployment requires replacing `MemorySessionStore` with a shared store (e.g., Redis). The `SessionStore` ABC already supports this — implement a new subclass, no other code changes needed.

---

## 9. Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_FILE_FORMAT",
    "message": "Unsupported file format: .docx. Supported formats: .xlsx, .xls, .csv"
  }
}
```

### Error Categories

| Scenario | HTTP Status | Error Code | User Message |
|---|---|---|---|
| Unsupported file format | 400 | `INVALID_FILE_FORMAT` | "Unsupported format. Please upload .xlsx, .xls, or .csv files." |
| File exceeds 5MB | 400 | `FILE_TOO_LARGE` | "File exceeds 5MB limit." |
| File has no data rows | 400 | `EMPTY_FILE` | "This file appears to be empty." |
| File can't be parsed | 400 | `PARSE_ERROR` | "Could not read this file. It may be corrupted." |
| Session not found | 404 | `SESSION_NOT_FOUND` | "Session expired. Please upload your files again." |
| DeepSeek API down | 502 | `LLM_UNAVAILABLE` | "Analysis service is temporarily unavailable. Please try again." |
| DeepSeek returns invalid JSON | 500 | `LLM_RESPONSE_ERROR` | "Something went wrong analyzing your data. Please try again." |
| Plan references bad column | 400 | `INVALID_ANALYSIS` | "Could not analyze: column 'X' not found in your data." |
| Plan references bad dataset | 400 | `INVALID_SOURCE` | "Could not find dataset 'X / Y' in your uploaded files." |
| Server at capacity | 503 | `SERVICE_AT_CAPACITY` | "Server is busy. Please try again in a few minutes." |
| Empty result | 200 | (no error) | "No data matches that criteria." |

### Client Error Handling

- Upload errors: inline message below dropzone, file stays for retry
- Chat errors: system message in chat history
- Loading states: spinner on upload, typing indicator on chat
- Network failure: "Connection lost. Please check your internet and try again."

### Retry Logic

- DeepSeek API failures: retry once with 2-second delay
- All other errors: no auto-retry

---

## 10. Not in MVP (Future Considerations)

- Authentication (email/password, OAuth)
- Session persistence (save/revisit past uploads and conversations)
- Sharing dashboards with others
- PDF table extraction
- Google Sheets integration
- Cross-file joins and relationships
- Larger file support (50MB+)
- Real-time collaboration
- Export charts as images or PDF reports
