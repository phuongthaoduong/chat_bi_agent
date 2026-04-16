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


class ChatRequest(BaseModel):
    session_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    chart: ChartDataResponse | None = None
    total_rows: int | None = None
    displayed_rows: int | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
