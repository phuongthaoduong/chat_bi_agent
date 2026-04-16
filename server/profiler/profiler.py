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
            if series.nunique() / max(len(series), 1) < 0.8:
                return "categorical"
            return "text"
        return "text"

    def _get_sample_values(self, series: pd.Series) -> list:
        non_null = series.dropna()
        dtype = self._infer_dtype(series)
        if dtype in ("categorical", "text"):
            # Return unique values so LLM can identify what this column holds (e.g. East/West/South)
            samples = non_null.unique()[:10].tolist()
        else:
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
