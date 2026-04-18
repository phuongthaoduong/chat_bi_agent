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

export interface ChartDataset {
  label: string;
  data: number[];
}

export interface ChartData {
  chart_type: string;
  title: string;
  labels: string[];
  datasets: ChartDataset[];
  x_axis?: string | null;
  y_axis?: string | null;
}

export interface UploadResponse {
  session_id: string;
  files: FileInfo[];
  profiles: SheetProfile[];
  warnings: string[];
  insights: string[];
  chart: ChartData | null;
}

export interface TableData {
  columns: string[];
  rows: unknown[][];
}

export interface ChatResponse {
  answer: string;
  chart: ChartData | null;
  table: TableData | null;
  total_rows?: number | null;
  displayed_rows?: number | null;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  chart?: ChartData | null;
  table?: TableData | null;
  totalRows?: number | null;
  displayedRows?: number | null;
}

export interface AddFilesResponse {
  files: FileInfo[];
  profiles: SheetProfile[];
  chart: ChartData | null;
  insights: string[];
  warnings: string[];
  replaced: string[];
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
  };
}
