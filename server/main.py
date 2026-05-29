import asyncio
import dataclasses
import logging
import uuid

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from analysis.engine import AnalysisEngine
from config import MAX_FILE_SIZE_BYTES, MAX_SESSIONS, SESSION_TTL_MINUTES
from models.api import (
    AddFilesResponse,
    ChatRequest,
    ChatResponse,
    ChartDataResponse,
    ColumnProfileResponse,
    ErrorDetail,
    ErrorResponse,
    FileInfo,
    SheetProfileResponse,
    TableDataResponse,
    UploadResponse,
)
from models.domain import DataSource, Message, ParsedFile, QuestionInterpretation, QuestionType, ResultType, SessionData
from parsers.registry import get_parser
from profiler.profiler import DataProfiler
from llm.relevance import is_obviously_irrelevant
from llm.constants import IRRELEVANT_REJECTION_MESSAGE
from session.memory_store import MemorySessionStore

logger = logging.getLogger(__name__)


async def _cleanup_loop():
    while True:
        await asyncio.sleep(300)  # every 5 minutes
        removed = session_store.cleanup_expired()
        if removed > 0:
            logger.info("Cleaned up %d expired session(s). Active: %d", removed, session_store.session_count())


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="ChatBI", lifespan=lifespan)

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
            _llm_client = LLMClient(timeout=30)
    return _llm_client


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
    chart_response: ChartDataResponse | None = None

    client = get_llm_client()
    if client:
        try:
            suggestion = client.suggest_dashboard(all_profiles)
            insights = suggestion.insights

            if suggestion.plan:
                try:
                    target_sheets = []
                    for pf in parsed_files:
                        if pf.name == suggestion.plan.source.file_name:
                            target_sheets = pf.sheets
                            break
                    if target_sheets:
                        result = analysis_engine.execute_plan(suggestion.plan, target_sheets)
                        if result.chart_data:
                            chart_response = ChartDataResponse(
                                chart_type=result.chart_data.chart_type,
                                title=result.chart_data.title,
                                labels=result.chart_data.labels,
                                datasets=result.chart_data.datasets,
                                x_axis=result.chart_data.x_axis,
                                y_axis=result.chart_data.y_axis,
                            )
                except Exception as e:
                    logger.warning("Failed to execute dashboard plan: %s", e)
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
        chart=chart_response,
    )


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

    logger.info("=== [STEP 1] Keyword filter: question=%r", request.question)
    session.chat_history.append(Message(role="user", content=request.question))

    try:
        logger.info("=== [STEP 2] Calling LLM to classify question...")
        interpretation = client.interpret_question(
            question=request.question,
            profiles=session.profiles,
            chat_history=session.chat_history,
        )
        logger.info("=== [STEP 2] LLM classified as: %s", interpretation.question_type.value)

        chart_response = None
        if interpretation.question_type == QuestionType.COMPUTATIONAL and interpretation.plan:
            logger.info("=== [STEP 3] Plan: %s", dataclasses.asdict(interpretation.plan))
            target_sheets = []
            for pf in session.files:
                if pf.name == interpretation.plan.source.file_name:
                    target_sheets = pf.sheets
                    break

            if not target_sheets:
                # Source not found — fall back to conversational answer
                logger.warning("=== [STEP 3] Source file not found, falling back to conversational")
                interpretation = QuestionInterpretation(question_type=QuestionType.CONVERSATIONAL, plan=None)
            else:
                try:
                    logger.info("=== [STEP 3] Executing plan against data...")
                    result = analysis_engine.execute_plan(interpretation.plan, target_sheets)
                    logger.info("=== [STEP 3] Result type: %s, data: %s", result.result_type.value, dataclasses.asdict(result.data))
                except ValueError as plan_err:
                    # Bad plan — retry LLM once with the error as feedback
                    logger.warning("=== [STEP 3] Bad plan (%s), retrying LLM...", plan_err)
                    # Build column list for retry context
                    valid_cols = []
                    for p in session.profiles:
                        for c in p.columns:
                            valid_cols.append(f'"{c.name}" ({c.dtype})')
                    plan_error_with_cols = (
                        f"{plan_err}\n"
                        f"Available columns: {', '.join(valid_cols)}"
                    )
                    interpretation = client.interpret_question(
                        question=request.question,
                        profiles=session.profiles,
                        chat_history=session.chat_history,
                        plan_error=plan_error_with_cols,
                    )
                    logger.info("=== [STEP 3] Retry classified as: %s", interpretation.question_type.value)
                    if interpretation.question_type == QuestionType.COMPUTATIONAL and interpretation.plan:
                        logger.info("=== [STEP 3] Retry plan: %s", dataclasses.asdict(interpretation.plan))
                        try:
                            result = analysis_engine.execute_plan(interpretation.plan, target_sheets)
                            logger.info("=== [STEP 3] Retry result: %s", dataclasses.asdict(result.data))
                        except ValueError as retry_err:
                            # Retry also failed (e.g. required column doesn't exist in the data)
                            # Fall back to conversational so the LLM can explain the data limitation
                            logger.warning("=== [STEP 3] Retry also failed (%s), falling back to conversational", retry_err)
                            interpretation = QuestionInterpretation(question_type=QuestionType.CONVERSATIONAL, plan=None)
                            result = None
                        except Exception as retry_err:
                            logger.warning("=== [STEP 3] Unexpected retry error (%s), falling back to conversational", retry_err)
                            interpretation = QuestionInterpretation(question_type=QuestionType.CONVERSATIONAL, plan=None)
                            result = None
                    else:
                        result = None
                except Exception as plan_err:
                    # Unexpected engine error (e.g. pandas KeyError, TypeError) — not a bad LLM
                    # plan, so don't retry; fall back to conversational instead of surfacing 502.
                    logger.warning("=== [STEP 3] Unexpected engine error (%s), falling back to conversational", plan_err)
                    interpretation = QuestionInterpretation(question_type=QuestionType.CONVERSATIONAL, plan=None)
                    result = None

                if interpretation.question_type == QuestionType.COMPUTATIONAL and interpretation.plan and result:
                    # Apply display cap for tabular results
                    total_rows = None
                    displayed_rows = None
                    if result.result_type == ResultType.TABULAR:
                        total_rows = len(result.data.rows)
                        if total_rows > 10_000:
                            displayed_rows = 10_000
                            result.data.rows = result.data.rows[:10_000]

                    logger.info("=== [STEP 4] Formatting answer with LLM...")
                    answer = client.format_answer(
                        question=request.question,
                        plan=interpretation.plan,
                        result=result,
                        profiles=session.profiles,
                        chat_history=session.chat_history,
                    )
                    logger.info("=== [STEP 4] Final answer: %s", answer)

                    if result.chart_data:
                        chart_response = ChartDataResponse(
                            chart_type=result.chart_data.chart_type,
                            title=result.chart_data.title,
                            labels=result.chart_data.labels,
                            datasets=result.chart_data.datasets,
                            x_axis=result.chart_data.x_axis,
                            y_axis=result.chart_data.y_axis,
                        )

                    table_response = None
                    if result.result_type == ResultType.TABULAR:
                        table_response = TableDataResponse(
                            columns=result.data.columns,
                            rows=result.data.rows,
                        )

                    session.chat_history.append(
                        Message(
                            role="assistant",
                            content=answer,
                            chart=chart_response.model_dump() if chart_response else None,
                        )
                    )
                    session_store.update(request.session_id, session)
                    return ChatResponse(answer=answer, chart=chart_response, table=table_response, total_rows=total_rows, displayed_rows=displayed_rows)

        logger.info("=== [STEP 4] Conversational answer — calling LLM to format...")
        answer = client.format_answer(
            question=request.question,
            plan=None,
            result=None,
            profiles=session.profiles,
            chat_history=session.chat_history,
        )
        logger.info("=== [STEP 4] Final answer: %s", answer)

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
    except Exception:
        logger.exception("Chat error")
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                error=ErrorDetail(code="LLM_UNAVAILABLE", message="Analysis service is temporarily unavailable.")
            ).model_dump(),
        )


@app.post("/api/session/{session_id}/files")
async def add_files_to_session(session_id: str, files: list[UploadFile] = File(...)):
    session = session_store.get(session_id)
    if session is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(code="SESSION_NOT_FOUND", message="Session expired. Please upload your files again.")
            ).model_dump(),
        )

    new_parsed_files: list[ParsedFile] = []
    new_profiles = []
    new_file_infos: list[FileInfo] = []
    warnings: list[str] = []
    replaced: list[str] = []

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

        # Replace existing file with same name if present
        existing_names = {pf.name for pf in session.files}
        if filename in existing_names:
            replaced.append(filename)
            session.files = [pf for pf in session.files if pf.name != filename]
            session.profiles = [p for p in session.profiles if p.source.file_name != filename]

        file_profiles = []
        for sheet in parsed.sheets:
            source = DataSource(file_name=filename, sheet_name=sheet.name)
            profile = profiler.profile(sheet, source)
            file_profiles.append(profile)
            new_file_infos.append(
                FileInfo(
                    name=filename,
                    sheet_name=sheet.name,
                    rows=profile.row_count,
                    columns=[c.name for c in profile.columns],
                )
            )

        session.files.append(parsed)
        session.profiles.extend(file_profiles)
        new_parsed_files.append(parsed)
        new_profiles.extend(file_profiles)

    # Generate dashboard chart for the newly added files only
    new_chart_response: ChartDataResponse | None = None
    new_insights: list[str] = []
    client = get_llm_client()
    if client and new_profiles:
        try:
            suggestion = client.suggest_dashboard(new_profiles)
            new_insights = suggestion.insights
            if suggestion.plan:
                try:
                    target_sheets = []
                    for pf in new_parsed_files:
                        if pf.name == suggestion.plan.source.file_name:
                            target_sheets = pf.sheets
                            break
                    if target_sheets:
                        result = analysis_engine.execute_plan(suggestion.plan, target_sheets)
                        if result.chart_data:
                            new_chart_response = ChartDataResponse(
                                chart_type=result.chart_data.chart_type,
                                title=result.chart_data.title,
                                labels=result.chart_data.labels,
                                datasets=result.chart_data.datasets,
                                x_axis=result.chart_data.x_axis,
                                y_axis=result.chart_data.y_axis,
                            )
                except Exception as e:
                    logger.warning("Failed to execute plan for added file: %s", e)
        except Exception as e:
            logger.warning("LLM dashboard generation failed for added file: %s", e)

    session_store.update(session_id, session)

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
        for p in new_profiles
    ]

    return AddFilesResponse(
        files=new_file_infos,
        profiles=profile_responses,
        chart=new_chart_response,
        insights=new_insights,
        warnings=warnings,
        replaced=replaced,
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
