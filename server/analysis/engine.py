import pandas as pd

from models.domain import (
    AnalysisIntent,
    AnalysisPlan,
    AnalysisResult,
    ChartData,
    FilterCondition,
    ListResult,
    ResultType,
    ScalarResult,
    SheetData,
    TabularResult,
)


class AnalysisEngine:
    def execute_plan(self, plan: AnalysisPlan, sheets: list[SheetData]) -> AnalysisResult:
        df = self._resolve_source(plan, sheets)
        df = self._apply_filters(df, plan.filters)

        if plan.intent == AnalysisIntent.AGGREGATE:
            result = self._aggregate(df, plan)
        elif plan.intent == AnalysisIntent.DISTRIBUTION:
            result = self._distribution(df, plan)
        elif plan.intent == AnalysisIntent.TREND:
            result = self._trend(df, plan)
        elif plan.intent == AnalysisIntent.COMPARISON:
            result = self._comparison(df, plan)
        elif plan.intent == AnalysisIntent.TOP_N:
            result = self._top_n(df, plan)
        elif plan.intent == AnalysisIntent.CORRELATION:
            result = self._correlation(df, plan)
        else:
            raise ValueError(f"Unknown intent: {plan.intent}")

        chart_data = self._build_chart_data(result, plan) if plan.chart else None

        return AnalysisResult(
            result_type=result[0],
            data=result[1],
            chart_data=chart_data,
        )

    def _resolve_source(self, plan: AnalysisPlan, sheets: list[SheetData]) -> pd.DataFrame:
        for sheet in sheets:
            if sheet.name == plan.source.sheet_name:
                self._validate_columns(sheet.df, plan)
                return sheet.df.copy()
        raise ValueError(
            f"Dataset not found: {plan.source.file_name} / {plan.source.sheet_name}"
        )

    def _validate_columns(self, df: pd.DataFrame, plan: AnalysisPlan) -> None:
        all_fields = set(plan.target_fields)
        if plan.group_by:
            all_fields.update(plan.group_by)
        if plan.filters:
            all_fields.update(f.field for f in plan.filters)
        if plan.sort:
            all_fields.add(plan.sort.field)

        missing = all_fields - set(df.columns)
        if missing:
            raise ValueError(f"Invalid column(s): {', '.join(sorted(missing))}")

        # Prevent groupby/target overlap which causes pandas "cannot insert X" error
        if plan.group_by and plan.intent in (
            AnalysisIntent.AGGREGATE, AnalysisIntent.TOP_N,
            AnalysisIntent.TREND, AnalysisIntent.COMPARISON,
        ):
            overlap = set(plan.target_fields) & set(plan.group_by)
            if overlap:
                raise ValueError(
                    f"Column(s) {overlap} cannot be used in both target_fields and group_by. "
                    f"Use a numeric column for target_fields and a categorical column for group_by."
                )

    def _apply_filters(
        self, df: pd.DataFrame, filters: list[FilterCondition] | None
    ) -> pd.DataFrame:
        if not filters:
            return df
        for f in filters:
            if f.operator == "eq":
                df = df[df[f.field] == f.value]
            elif f.operator == "ne":
                df = df[df[f.field] != f.value]
            elif f.operator == "gt":
                df = df[df[f.field] > f.value]
            elif f.operator == "lt":
                df = df[df[f.field] < f.value]
            elif f.operator == "gte":
                df = df[df[f.field] >= f.value]
            elif f.operator == "lte":
                df = df[df[f.field] <= f.value]
            elif f.operator == "in":
                df = df[df[f.field].isin(f.value)]
            elif f.operator == "contains":
                df = df[df[f.field].astype(str).str.contains(str(f.value), case=False, na=False)]
        return df

    def _aggregate(self, df: pd.DataFrame, plan: AnalysisPlan):
        target = plan.target_fields[0]
        if plan.group_by:
            grouped = df.groupby(plan.group_by)[target].sum().reset_index()
            if plan.sort:
                grouped = grouped.sort_values(
                    plan.sort.field, ascending=(plan.sort.direction == "asc")
                )
            if plan.limit:
                grouped = grouped.head(plan.limit)
            items = [
                {"label": str(row[plan.group_by[0]]), "value": self._serialize(row[target])}
                for _, row in grouped.iterrows()
            ]
            return (ResultType.LIST, ListResult(items=items))
        else:
            total = self._serialize(df[target].sum())
            return (ResultType.SCALAR, ScalarResult(label=f"Total {target}", value=total))

    def _distribution(self, df: pd.DataFrame, plan: AnalysisPlan):
        target = plan.target_fields[0]
        counts = df[target].value_counts()
        if plan.limit:
            counts = counts.head(plan.limit)
        items = [{"label": str(v), "value": int(c)} for v, c in counts.items()]
        return (ResultType.LIST, ListResult(items=items))

    def _trend(self, df: pd.DataFrame, plan: AnalysisPlan):
        target = plan.target_fields[0]
        group_col = plan.group_by[0] if plan.group_by else target
        grouped = df.groupby(group_col)[target].sum().reset_index()
        items = [
            {"label": str(row[group_col]), "value": self._serialize(row[target])}
            for _, row in grouped.iterrows()
        ]
        return (ResultType.LIST, ListResult(items=items))

    def _comparison(self, df: pd.DataFrame, plan: AnalysisPlan):
        return self._aggregate(df, plan)

    def _top_n(self, df: pd.DataFrame, plan: AnalysisPlan):
        target = plan.target_fields[0]
        group_col = plan.group_by[0] if plan.group_by else target

        if plan.group_by:
            grouped = df.groupby(group_col)[target].sum().reset_index()
        else:
            grouped = df[[target]].copy()
            grouped[group_col] = grouped[target].astype(str)

        sort_dir = plan.sort.direction if plan.sort else "desc"
        grouped = grouped.sort_values(target, ascending=(sort_dir == "asc"))
        limit = plan.limit or 5
        grouped = grouped.head(limit)

        items = [
            {"label": str(row[group_col]), "value": self._serialize(row[target])}
            for _, row in grouped.iterrows()
        ]
        return (ResultType.LIST, ListResult(items=items))

    def _correlation(self, df: pd.DataFrame, plan: AnalysisPlan):
        if len(plan.target_fields) < 2:
            raise ValueError("Correlation requires at least 2 target fields")
        f1, f2 = plan.target_fields[0], plan.target_fields[1]
        rows = [
            [self._serialize(row[f1]), self._serialize(row[f2])]
            for _, row in df[[f1, f2]].dropna().iterrows()
        ]
        return (ResultType.TABULAR, TabularResult(columns=[f1, f2], rows=rows))

    def _build_chart_data(self, result: tuple, plan: AnalysisPlan) -> ChartData:
        result_type, data = result
        labels = []
        datasets = []

        if isinstance(data, ListResult):
            labels = [item["label"] for item in data.items]
            datasets = [
                {"label": plan.target_fields[0], "data": [item["value"] for item in data.items]}
            ]
        elif isinstance(data, TabularResult):
            labels = [str(r[0]) for r in data.rows]
            datasets = [{"label": data.columns[1], "data": [r[1] for r in data.rows]}]

        return ChartData(
            chart_type=plan.chart.chart_type,
            title=plan.chart.title,
            labels=labels,
            datasets=datasets,
            x_axis=plan.chart.x_axis,
            y_axis=plan.chart.y_axis,
        )

    def _serialize(self, value):
        if hasattr(value, "item"):
            return value.item()
        return value
