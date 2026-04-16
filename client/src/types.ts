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
  charts: ChartData[];
}

export interface ChatResponse {
  answer: string;
  chart: ChartData | null;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  chart?: ChartData | null;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
  };
}
