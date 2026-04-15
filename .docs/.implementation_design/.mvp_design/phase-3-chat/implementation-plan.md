# Phase 3: Chat — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** User can ask follow-up questions about their data and get answers (with charts when relevant). Supports both computational questions (grounded in real data) and conversational questions (interpretive).

**Architecture:** Two-call LLM pattern for computational questions (classify → compute → narrate). Single-call for conversational questions. Question classification determines the path.

**Tech Stack:** DeepSeek API, existing analysis engine, React chat UI

**Depends on:** Phase 2 completed

---

## What the User Can Test After This Phase

1. Upload a file → see dashboard → type a question like "What product sold the most?"
2. Get a text answer grounded in real computed data + a chart
3. Ask an interpretive question like "What does this trend mean?" → get a text answer (no chart)
4. See conversation history
5. Toggle between dashboard view and chat view

---

## File Structure (New/Modified)

### Server

```
server/
├── llm/
│   ├── client.py               # Add: interpret_question(), format_answer()
│   └── prompts.py              # Add: chat prompts (classify, format)
├── models/
│   ├── api.py                  # Add: ChatRequest, ChatResponse
│   └── domain.py               # Add: QuestionType, QuestionInterpretation
└── main.py                     # Add: POST /api/chat, GET /api/session/{id}
```

### Client

```
client/src/
├── api.ts                      # Add: askQuestion()
├── types.ts                    # Add: ChatResponse, Message
├── components/
│   ├── session/
│   │   ├── SessionScreen.tsx   # Modify: add chat state, view toggle
│   │   ├── ChatView.tsx        # NEW
│   │   └── ViewToggle.tsx      # NEW
│   └── shared/
│       ├── ChatInput.tsx       # NEW
│       └── ChatMessage.tsx     # NEW
```

---

## Tasks

### Task 1: Chat Domain Models & Prompts

**Files:**
- Modify: `server/models/domain.py`
- Modify: `server/llm/prompts.py`

- [ ] **Step 1: Add chat types to domain.py**

Append to `server/models/domain.py`:
```python
class QuestionType(Enum):
    COMPUTATIONAL = "computational"
    CONVERSATIONAL = "conversational"


@dataclass
class QuestionInterpretation:
    question_type: QuestionType
    plan: AnalysisPlan | None  # null for conversational
```

- [ ] **Step 2: Add chat prompts to prompts.py**

Append to `server/llm/prompts.py`:
```python
CHAT_CLASSIFY_PROMPT = """You are a data analyst. Given the dataset schemas and the user's question, first classify the question, then produce an analysis plan if needed.

AVAILABLE DATASETS:
{dataset_inventory}

DETAILED SCHEMA:
{profile_detail}

CHAT HISTORY:
{chat_history}

USER QUESTION:
{question}

Respond with EXACTLY this JSON structure (no markdown, no code fences):
{{
  "question_type": "computational" or "conversational",
  "plan": {{
    "source": {{ "file_name": "...", "sheet_name": "..." }},
    "intent": "aggregate|distribution|trend|comparison|top_n|correlation",
    "target_fields": ["column_name"],
    "group_by": ["column_name"] or null,
    "filters": [{{"field": "...", "operator": "eq|ne|gt|lt|gte|lte|in|contains", "value": "..."}}] or null,
    "sort": {{"field": "...", "direction": "asc|desc"}} or null,
    "limit": number or null,
    "chart": {{
      "chart_type": "bar|line|pie|scatter",
      "title": "string",
      "x_axis": "column_name" or null,
      "y_axis": "column_name" or null
    }} or null
  }} or null
}}

RULES:
- Classify as "computational" if the question requires querying data (aggregations, filtering, ranking, comparisons, trends)
- Classify as "conversational" if the question is interpretive (explaining charts, summarizing patterns, asking "why", general advice)
- If "computational", plan MUST include a valid "source" and column references from the schema
- If "conversational", set plan to null
- Do NOT include any answer text"""


CHAT_FORMAT_COMPUTATIONAL_PROMPT = """You are a data analyst assistant. The user asked a question and the system has computed the result. Write a clear, concise answer based on the actual data provided.

USER QUESTION:
{question}

COMPUTED RESULT:
{result_json}

RULES:
- Only state facts that appear in the computed result
- Do not invent or estimate numbers
- Keep the answer to 1-3 sentences
- Use natural language appropriate for a non-technical business user"""


CHAT_FORMAT_CONVERSATIONAL_PROMPT = """You are a data analyst assistant. The user asked an interpretive question. Answer based on the dataset context and conversation history provided.

AVAILABLE DATASETS:
{dataset_inventory}

DETAILED SCHEMA:
{profile_detail}

RECENT CHAT HISTORY (including prior computed results):
{chat_history}

USER QUESTION:
{question}

RULES:
- Base your answer on the dataset profile and prior computed results in chat history
- Do not invent specific numbers unless they appear in the provided context
- Clearly distinguish interpretation from established fact
- Keep the answer to 2-4 sentences
- Use natural language appropriate for a non-technical business user"""


def format_chat_history(messages: list) -> str:
    if not messages:
        return "(no prior messages)"
    lines = []
    for msg in messages[-10:]:  # last 10 messages for context window
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)
```

- [ ] **Step 3: Commit**

```bash
git add server/models/domain.py server/llm/prompts.py
git commit -m "feat: add chat question types and prompt templates"
```

---

### Task 2: LLM Client — Chat Methods

**Files:**
- Modify: `server/llm/client.py`
- Create: `server/tests/test_llm_chat.py`

- [ ] **Step 1: Write the failing tests**

Create `server/tests/test_llm_chat.py`:
```python
import json

import pytest

from llm.client import parse_question_interpretation
from models.domain import AnalysisIntent, QuestionType


def test_parse_computational_question():
    raw = json.dumps(
        {
            "question_type": "computational",
            "plan": {
                "source": {"file_name": "sales.csv", "sheet_name": "Sheet1"},
                "intent": "top_n",
                "target_fields": ["sales"],
                "group_by": ["product"],
                "filters": None,
                "sort": {"field": "sales", "direction": "desc"},
                "limit": 5,
                "chart": {
                    "chart_type": "bar",
                    "title": "Top 5 Products",
                    "x_axis": "product",
                    "y_axis": "sales",
                },
            },
        }
    )
    result = parse_question_interpretation(raw)
    assert result.question_type == QuestionType.COMPUTATIONAL
    assert result.plan is not None
    assert result.plan.intent == AnalysisIntent.TOP_N
    assert result.plan.limit == 5


def test_parse_conversational_question():
    raw = json.dumps(
        {
            "question_type": "conversational",
            "plan": None,
        }
    )
    result = parse_question_interpretation(raw)
    assert result.question_type == QuestionType.CONVERSATIONAL
    assert result.plan is None


def test_parse_invalid_json():
    with pytest.raises(ValueError, match="Invalid"):
        parse_question_interpretation("not json")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && python -m pytest tests/test_llm_chat.py -v`
Expected: FAIL

- [ ] **Step 3: Add parse_question_interpretation and chat methods to client.py**

Add to `server/llm/client.py`:
```python
import dataclasses

from llm.prompts import (
    CHAT_CLASSIFY_PROMPT,
    CHAT_FORMAT_COMPUTATIONAL_PROMPT,
    CHAT_FORMAT_CONVERSATIONAL_PROMPT,
    format_chat_history,
)
from models.domain import (
    AnalysisResult,
    Message,
    QuestionInterpretation,
    QuestionType,
)


def parse_question_interpretation(raw: str) -> QuestionInterpretation:
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

    question_type = QuestionType(data["question_type"])

    plan = None
    if data.get("plan"):
        p = data["plan"]
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
        plan = AnalysisPlan(
            source=source,
            intent=AnalysisIntent(p["intent"]),
            target_fields=p["target_fields"],
            group_by=p.get("group_by"),
            filters=filters,
            sort=sort,
            limit=p.get("limit"),
            chart=chart,
        )

    return QuestionInterpretation(question_type=question_type, plan=plan)
```

Add methods to `LLMClient` class:
```python
    def interpret_question(
        self,
        question: str,
        profiles: list[SheetProfile],
        chat_history: list[Message],
    ) -> QuestionInterpretation:
        inventory = build_dataset_inventory(profiles)
        detail = build_profile_detail(profiles)
        history = format_chat_history(chat_history)

        prompt = CHAT_CLASSIFY_PROMPT.format(
            dataset_inventory=inventory,
            profile_detail=detail,
            chat_history=history,
            question=question,
        )

        response = self._client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        raw = response.choices[0].message.content
        logger.info("LLM classify response: %s", raw)

        try:
            return parse_question_interpretation(raw)
        except (ValueError, KeyError) as e:
            logger.warning("First classify parse failed (%s), retrying...", e)
            response = self._client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": "Your response was not valid JSON. Please respond with ONLY the JSON structure, no markdown.",
                    },
                ],
                temperature=0.1,
            )
            raw = response.choices[0].message.content
            return parse_question_interpretation(raw)

    def format_answer(
        self,
        question: str,
        plan: AnalysisPlan | None,
        result: AnalysisResult | None,
        profiles: list[SheetProfile],
        chat_history: list[Message],
    ) -> str:
        if plan and result:
            # Computational path
            result_json = json.dumps(self._serialize_result(result), indent=2)
            prompt = CHAT_FORMAT_COMPUTATIONAL_PROMPT.format(
                question=question,
                result_json=result_json,
            )
        else:
            # Conversational path
            inventory = build_dataset_inventory(profiles)
            detail = build_profile_detail(profiles)
            history = format_chat_history(chat_history)
            prompt = CHAT_FORMAT_CONVERSATIONAL_PROMPT.format(
                dataset_inventory=inventory,
                profile_detail=detail,
                chat_history=history,
                question=question,
            )

        response = self._client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def _serialize_result(self, result: AnalysisResult) -> dict:
        data = result.data
        if hasattr(data, "items"):
            return {"type": "list", "items": data.items}
        elif hasattr(data, "value"):
            return {"type": "scalar", "label": data.label, "value": data.value}
        elif hasattr(data, "rows"):
            return {"type": "table", "columns": data.columns, "rows": data.rows}
        return {}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_llm_chat.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add server/llm/client.py server/tests/test_llm_chat.py
git commit -m "feat: add LLM chat methods with classify and format answer"
```

---

### Task 3: Chat API Endpoint

**Files:**
- Modify: `server/models/api.py`
- Modify: `server/main.py`
- Create: `server/tests/test_chat_api.py`

- [ ] **Step 1: Add chat API models**

Add to `server/models/api.py`:
```python
class ChatRequest(BaseModel):
    session_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    chart: ChartDataResponse | None = None
```

- [ ] **Step 2: Write the failing test**

Create `server/tests/test_chat_api.py`:
```python
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from models.domain import (
    AnalysisIntent,
    AnalysisPlan,
    ChartSpec,
    DataSource,
    QuestionInterpretation,
    QuestionType,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _upload_file(client):
    content = (FIXTURES / "sample.csv").read_bytes()
    response = await client.post(
        "/api/upload",
        files={"files": ("sample.csv", content, "text/csv")},
    )
    return response.json()["session_id"]


@pytest.mark.anyio
async def test_chat_missing_session():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "nonexistent", "question": "hello"},
        )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.anyio
async def test_chat_without_llm_key():
    """When no LLM key is set, chat returns an error gracefully."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        session_id = await _upload_file(client)
        response = await client.post(
            "/api/chat",
            json={"session_id": session_id, "question": "What is the total sales?"},
        )
    # Without LLM key, should return error
    assert response.status_code in (200, 502)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd server && python -m pytest tests/test_chat_api.py -v`
Expected: FAIL

- [ ] **Step 4: Implement chat endpoint**

Add to `server/main.py`:
```python
from models.api import ChatRequest, ChatResponse, ChartDataResponse
from models.domain import Message, QuestionType


@app.post("/api/chat")
async def chat(request: ChatRequest):
    session = session_store.get(request.session_id)
    if session is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(code="SESSION_NOT_FOUND", message="Session expired. Please upload your files again.")
            ).model_dump(),
        )

    client = get_llm_client()
    if client is None:
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                error=ErrorDetail(code="LLM_UNAVAILABLE", message="Analysis service is not configured.")
            ).model_dump(),
        )

    # Add user message to history
    session.chat_history.append(Message(role="user", content=request.question))

    try:
        # Call 1: Classify and interpret
        interpretation = client.interpret_question(
            question=request.question,
            profiles=session.profiles,
            chat_history=session.chat_history,
        )

        chart_response = None
        if interpretation.question_type == QuestionType.COMPUTATIONAL and interpretation.plan:
            # Find sheets for the plan's source
            target_sheets = []
            for pf in session.files:
                if pf.name == interpretation.plan.source.file_name:
                    target_sheets = pf.sheets
                    break

            if not target_sheets:
                return JSONResponse(
                    status_code=400,
                    content=ErrorResponse(
                        error=ErrorDetail(
                            code="INVALID_SOURCE",
                            message=f"Could not find dataset '{interpretation.plan.source.file_name} / {interpretation.plan.source.sheet_name}' in your uploaded files.",
                        )
                    ).model_dump(),
                )

            # Execute the plan
            result = analysis_engine.execute_plan(interpretation.plan, target_sheets)

            # Call 2: Format answer with real data
            answer = client.format_answer(
                question=request.question,
                plan=interpretation.plan,
                result=result,
                profiles=session.profiles,
                chat_history=session.chat_history,
            )

            if result.chart_data:
                chart_response = ChartDataResponse(
                    chart_type=result.chart_data.chart_type,
                    title=result.chart_data.title,
                    labels=result.chart_data.labels,
                    datasets=result.chart_data.datasets,
                    x_axis=result.chart_data.x_axis,
                    y_axis=result.chart_data.y_axis,
                )
        else:
            # Conversational path
            answer = client.format_answer(
                question=request.question,
                plan=None,
                result=None,
                profiles=session.profiles,
                chat_history=session.chat_history,
            )

        # Add assistant message to history
        session.chat_history.append(
            Message(
                role="assistant",
                content=answer,
                chart=chart_response.model_dump() if chart_response else None,
            )
        )
        session_store.update(request.session_id, session)

        return ChatResponse(answer=answer, chart=chart_response)

    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(code="INVALID_ANALYSIS", message=str(e))
            ).model_dump(),
        )
    except Exception as e:
        import logging
        logging.exception("Chat error")
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                error=ErrorDetail(code="LLM_UNAVAILABLE", message="Analysis service is temporarily unavailable. Please try again.")
            ).model_dump(),
        )


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    session = session_store.get(session_id)
    if session is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(code="SESSION_NOT_FOUND", message="Session expired. Please upload your files again.")
            ).model_dump(),
        )

    file_infos = []
    profile_responses = []
    for profile in session.profiles:
        file_infos.append(
            FileInfo(
                name=profile.source.file_name,
                sheet_name=profile.source.sheet_name,
                rows=profile.row_count,
                columns=[c.name for c in profile.columns],
            )
        )
        profile_responses.append(
            SheetProfileResponse(
                file_name=profile.source.file_name,
                sheet_name=profile.source.sheet_name,
                row_count=profile.row_count,
                column_count=profile.column_count,
                columns=[
                    ColumnProfileResponse(
                        name=c.name, dtype=c.dtype, null_count=c.null_count,
                        null_pct=c.null_pct, unique_count=c.unique_count,
                        sample_values=c.sample_values, stats=c.stats,
                    )
                    for c in profile.columns
                ],
            )
        )

    return UploadResponse(
        session_id=session_id,
        files=file_infos,
        profiles=profile_responses,
        warnings=[],
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd server && python -m pytest tests/test_chat_api.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add server/main.py server/models/api.py server/tests/test_chat_api.py
git commit -m "feat: add POST /api/chat and GET /api/session endpoints"
```

---

### Task 4: Client Chat Types & API

**Files:**
- Modify: `client/src/types.ts`
- Modify: `client/src/api.ts`

- [ ] **Step 1: Add chat types**

Add to `client/src/types.ts`:
```typescript
export interface ChatResponse {
  answer: string;
  chart: ChartData | null;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  chart?: ChartData | null;
}
```

- [ ] **Step 2: Add askQuestion to api.ts**

Add to `client/src/api.ts`:
```typescript
import { UploadResponse, ChatResponse } from "./types";

export async function askQuestion(
  sessionId: string,
  question: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || "Chat request failed");
  }

  return response.json();
}
```

- [ ] **Step 3: Commit**

```bash
git add client/src/types.ts client/src/api.ts
git commit -m "feat: add chat types and API client"
```

---

### Task 5: Chat UI Components

**Files:**
- Create: `client/src/components/shared/ChatInput.tsx`
- Create: `client/src/components/shared/ChatMessage.tsx`
- Create: `client/src/components/session/ChatView.tsx`
- Create: `client/src/components/session/ViewToggle.tsx`

- [ ] **Step 1: Create ChatInput component**

Create `client/src/components/shared/ChatInput.tsx`:
```tsx
import { useState, KeyboardEvent } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, isLoading, placeholder }: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    const trimmed = value.trim();
    if (trimmed && !isLoading) {
      onSend(trimmed);
      setValue("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: "flex", gap: "8px", padding: "16px 24px", borderTop: "1px solid #e5e7eb" }}>
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || "Ask a question about your data..."}
        disabled={isLoading}
        style={{
          flex: 1,
          padding: "10px 16px",
          border: "1px solid #d1d5db",
          borderRadius: "8px",
          fontSize: "14px",
          outline: "none",
        }}
      />
      <button
        onClick={handleSend}
        disabled={isLoading || !value.trim()}
        style={{
          padding: "10px 20px",
          backgroundColor: isLoading ? "#9ca3af" : "#4f46e5",
          color: "white",
          border: "none",
          borderRadius: "8px",
          cursor: isLoading ? "wait" : "pointer",
          fontSize: "14px",
        }}
      >
        {isLoading ? "..." : "Send"}
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Create ChatMessage component**

Create `client/src/components/shared/ChatMessage.tsx`:
```tsx
import { Message } from "../../types";
import { ChartCard } from "./ChartCard";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "16px",
      }}
    >
      <div
        style={{
          maxWidth: "80%",
          padding: "12px 16px",
          borderRadius: "12px",
          backgroundColor: isUser ? "#4f46e5" : "#f3f4f6",
          color: isUser ? "white" : "#111827",
          fontSize: "14px",
          lineHeight: "1.5",
        }}
      >
        <p style={{ margin: 0 }}>{message.content}</p>
        {message.chart && (
          <div style={{ marginTop: "12px" }}>
            <ChartCard data={message.chart} />
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create ChatView component**

Create `client/src/components/session/ChatView.tsx`:
```tsx
import { useRef, useEffect } from "react";
import { Message } from "../../types";
import { ChatMessage } from "../shared/ChatMessage";
import { ChatInput } from "../shared/ChatInput";

interface ChatViewProps {
  messages: Message[];
  onSend: (message: string) => void;
  isLoading: boolean;
}

export function ChatView({ messages, onSend, isLoading }: ChatViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 120px)" }}>
      <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "#9ca3af", marginTop: "48px" }}>
            <p>Ask a question about your data</p>
            <p style={{ fontSize: "14px" }}>
              Try: "What product sold the most?" or "Show me monthly trends"
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
        {isLoading && (
          <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "16px" }}>
            <div
              style={{
                padding: "12px 16px",
                borderRadius: "12px",
                backgroundColor: "#f3f4f6",
                color: "#6b7280",
                fontSize: "14px",
              }}
            >
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={onSend} isLoading={isLoading} />
    </div>
  );
}
```

- [ ] **Step 4: Create ViewToggle component**

Create `client/src/components/session/ViewToggle.tsx`:
```tsx
interface ViewToggleProps {
  activeView: "dashboard" | "chat";
  onToggle: (view: "dashboard" | "chat") => void;
}

export function ViewToggle({ activeView, onToggle }: ViewToggleProps) {
  return (
    <div style={{ display: "flex", gap: "4px", padding: "8px", backgroundColor: "#f3f4f6", borderRadius: "8px" }}>
      {(["dashboard", "chat"] as const).map((view) => (
        <button
          key={view}
          onClick={() => onToggle(view)}
          style={{
            padding: "6px 16px",
            border: "none",
            borderRadius: "6px",
            fontSize: "14px",
            cursor: "pointer",
            backgroundColor: activeView === view ? "white" : "transparent",
            color: activeView === view ? "#111827" : "#6b7280",
            boxShadow: activeView === view ? "0 1px 2px rgba(0,0,0,0.1)" : "none",
          }}
        >
          {view === "dashboard" ? "Dashboard" : "Chat"}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add client/src/components/
git commit -m "feat: add ChatView, ChatInput, ChatMessage, and ViewToggle components"
```

---

### Task 6: Wire Chat into SessionScreen

**Files:**
- Modify: `client/src/components/session/SessionScreen.tsx`

- [ ] **Step 1: Update SessionScreen with chat state and view toggle**

Replace `client/src/components/session/SessionScreen.tsx`:
```tsx
import { useState } from "react";
import { askQuestion } from "../../api";
import { Message, UploadResponse } from "../../types";
import { FileInfoBar } from "./FileInfoBar";
import { DashboardView } from "./DashboardView";
import { ChatView } from "./ChatView";
import { ViewToggle } from "./ViewToggle";
import { ChatInput } from "../shared/ChatInput";

interface SessionScreenProps {
  data: UploadResponse;
  onReset: () => void;
}

export function SessionScreen({ data, onReset }: SessionScreenProps) {
  const [activeView, setActiveView] = useState<"dashboard" | "chat">("dashboard");
  const [chatHistory, setChatHistory] = useState<Message[]>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);

  const handleSendMessage = async (question: string) => {
    const userMessage: Message = { role: "user", content: question };
    setChatHistory((prev) => [...prev, userMessage]);
    setIsChatLoading(true);
    setActiveView("chat");

    try {
      const response = await askQuestion(data.session_id, question);
      const assistantMessage: Message = {
        role: "assistant",
        content: response.answer,
        chart: response.chart,
      };
      setChatHistory((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: Message = {
        role: "assistant",
        content: err instanceof Error ? err.message : "Something went wrong. Please try again.",
      };
      setChatHistory((prev) => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
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
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <ViewToggle activeView={activeView} onToggle={setActiveView} />
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
      </div>
      <FileInfoBar profiles={data.profiles} warnings={data.warnings} />

      {activeView === "dashboard" ? (
        <div style={{ flex: 1 }}>
          <DashboardView insights={data.insights} charts={data.charts} />
          <ChatInput onSend={handleSendMessage} isLoading={isChatLoading} />
        </div>
      ) : (
        <ChatView
          messages={chatHistory}
          onSend={handleSendMessage}
          isLoading={isChatLoading}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Test end-to-end**

1. Set `DEEPSEEK_API_KEY` and start server + client
2. Upload a CSV → see dashboard
3. Type "What product sold the most?" in the chat input
4. Expect: view switches to chat, answer appears with a chart
5. Type "What does this mean?" → expect text-only answer
6. Click "Dashboard" toggle → back to chart view
7. Click "Chat" toggle → see conversation history

- [ ] **Step 3: Commit**

```bash
git add client/src/components/session/SessionScreen.tsx
git commit -m "feat: wire chat into SessionScreen with view toggle"
```

---

## Phase 3 Completion Checklist

- [ ] Upload file → see dashboard → type computational question → get answer with chart
- [ ] Ask interpretive question → get text-only answer
- [ ] Conversation history is preserved
- [ ] Toggle between dashboard and chat views
- [ ] Chat from dashboard view auto-switches to chat view
- [ ] "Thinking..." indicator shows while waiting for response
- [ ] Error messages appear as system messages in chat
- [ ] All server tests pass: `cd server && python -m pytest -v`
