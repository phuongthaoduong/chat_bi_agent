import logging
import uuid
from io import BytesIO

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from analysis.engine import AnalysisEngine
from config import MAX_FILE_SIZE_BYTES, MAX_SESSIONS, SESSION_TTL_MINUTES
from models.api import (
    ChartDataResponse,
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

logger = logging.getLogger(__name__)

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
analysis_engine = AnalysisEngine()

_llm_client = None


def get_llm_client():
    global _llm_client
    if _llm_client is None:
        from config import DEEPSEEK_API_KEY
        if DEEPSEEK_API_KEY:
            from llm.client import LLMClient
            _llm_client = LLMClient()
    return _llm_client


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...)):
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

        try:
            parser = get_parser(filename)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="INVALID_FILE_FORMAT",
                        message="Unsupported format. Please upload .xlsx, .xls, or .csv files.",
                    )
                ).model_dump(),
            )

        content = await upload_file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error=ErrorDetail(code="FILE_TOO_LARGE", message="File exceeds 5MB limit.")
                ).model_dump(),
            )

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
    try:
        session_store.create(session_id, session_data)
    except RuntimeError:
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ErrorDetail(code="SERVICE_AT_CAPACITY", message="Server is busy. Please try again in a few minutes.")
            ).model_dump(),
        )

    # Generate dashboard via LLM (graceful degradation if unavailable)
    insights: list[str] = []
    chart_responses: list[ChartDataResponse] = []

    client = get_llm_client()
    if client:
        try:
            suggestion = client.suggest_dashboard(all_profiles)
            insights = suggestion.insights

            for plan in suggestion.plans:
                try:
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
                    logger.warning("Failed to execute plan: %s", e)
                    continue
        except Exception as e:
            logger.warning("LLM dashboard generation failed: %s", e)

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
        insights=insights,
        charts=chart_responses,
    )
