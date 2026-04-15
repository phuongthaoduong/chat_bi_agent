# ChatBI MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web app where users upload data files, get an auto-generated dashboard, and chat with their data.

**Architecture:** Monolith — React/Vite SPA + Python FastAPI server + DeepSeek API. LLM produces structured analysis plans (never code). Two-call LLM pattern for chat ensures answer correctness.

**Tech Stack:** React 18, Vite, TypeScript, ECharts | Python 3.11+, FastAPI, pandas, openpyxl, xlrd, chardet | DeepSeek API

**Spec:** `.docs/.architectture_design/architecture-design.md`

---

## Milestones

Each phase produces something testable from a user perspective.

| Phase | What the User Can Test | Key Deliverables |
|---|---|---|
| **1. Upload & Parse** | Upload CSV/Excel → see file structure, columns, types, stats | Server parsers, profiler, session store, client upload UI, file info display |
| **2. Auto Dashboard** | Upload file → see auto-generated charts and insights | DeepSeek integration, analysis engine, ECharts rendering, dashboard UI |
| **3. Chat** | Ask follow-up questions → get answers with charts | Question classification, two-call LLM pattern, chat UI, view toggle |
| **4. Polish & Resilience** | Robust error messages, loading states, session cleanup, multi-file support | Error handling, session TTL, capacity limits, display cap, warnings |

## Phase Dependencies

```
Phase 1 (Upload & Parse)
    ↓
Phase 2 (Auto Dashboard)
    ↓
Phase 3 (Chat)
    ↓
Phase 4 (Polish & Resilience)
```

Each phase builds on the previous. No phase can be skipped.
