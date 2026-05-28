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
        elif plan.intent == AnalysisIntent.AVERAGE:
            result = self._average(df, plan)
        elif plan.intent == AnalysisIntent.COUNT:
            result = self._count(df, plan)
        elif plan.intent == AnalysisIntent.DETAIL:
            result = self._detail(df, plan)
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

    def _remap_col(self, name: str, df: pd.DataFrame) -> str:
        """Return the actual column name in df that fuzzy-matches `name`, or `name` unchanged."""
        if name in df.columns:
            return name
        key_to_actual = {self._col_key(c): c for c in df.columns}
        return key_to_actual.get(self._col_key(name), name)

    def _resolve_source(self, plan: AnalysisPlan, sheets: list[SheetData]) -> pd.DataFrame:
        # Find primary sheet
        df = None
        for sheet in sheets:
            if sheet.name == plan.source.sheet_name:
                df = sheet.df.copy()
                break
        if df is None:
            raise ValueError(
                f"Dataset not found: {plan.source.file_name} / {plan.source.sheet_name}"
            )

        # Apply join if specified
        if plan.join:
            join_df = None
            for sheet in sheets:
                if sheet.name == plan.join.sheet_name:
                    join_df = sheet.df.copy()
                    break
            if join_df is None:
                raise ValueError(f"Join sheet not found: {plan.join.sheet_name}")

            # Normalize in place (plan objects are consumed by execute_plan; callers must not re-use them)
            # Remap the join key independently for each side so that different case/spacing
            # variants (e.g. "Product ID" vs "ProductID") are handled correctly.
            df_on = self._remap_col(plan.join.on, df)
            join_on = self._remap_col(plan.join.on, join_df)
            plan.join.on = join_on
            plan.join.columns = [self._remap_col(c, join_df) for c in plan.join.columns]

            # Build list of columns to pull from join sheet (key + requested columns, deduplicated)
            pull_cols = [join_on] + [c for c in plan.join.columns if c != join_on]
            pull_cols = [c for c in pull_cols if c in join_df.columns]

            # Left-merge; drop_duplicates on key to avoid row multiplication.
            # Use left_on/right_on so the merge works even when the key has a different
            # name in each sheet; drop the redundant right-side key column afterwards.
            df = df.merge(
                join_df[pull_cols].drop_duplicates(subset=[join_on]),
                left_on=df_on,
                right_on=join_on,
                how="left",
            )
            if df_on != join_on and join_on in df.columns:
                df = df.drop(columns=[join_on])

        self._normalize_plan_columns(df, plan)
        self._validate_columns(df, plan)
        return df

    @staticmethod
    def _col_key(name: str) -> str:
        """Normalize a column name for fuzzy matching: lowercase + underscores."""
        return name.lower().replace(" ", "_").replace("-", "_")

    def _normalize_plan_columns(self, df: pd.DataFrame, plan: AnalysisPlan) -> None:
        """
        Remap column names in the plan to their actual DataFrame counterparts when
        an exact match fails but a case/space-insensitive match succeeds.
        e.g. LLM emits "product_category" but the real column is "Product Category".

        Also self-heals plans where the LLM used "count" as a fake column name:
        e.g. intent="top_n", target_fields=["count"] → intent="count", target_fields=[]
        Mutates plan in place.
        """
        # Heal: LLM used "count" as a column name instead of using intent="count"
        _COUNT_ALIASES = {"count", "order_count", "num_orders", "number_of_orders", "frequency"}

        def _is_count_alias(name: str) -> bool:
            return name.lower().replace(" ", "_") in _COUNT_ALIASES

        # Case 1: wrong intent with fake count column (e.g. intent="top_n", target_fields=["count"])
        if (
            plan.intent in (AnalysisIntent.TOP_N, AnalysisIntent.AGGREGATE, AnalysisIntent.COMPARISON)
            and plan.target_fields
            and all(_is_count_alias(f) for f in plan.target_fields)
            and not any(f in df.columns for f in plan.target_fields)
        ):
            plan.intent = AnalysisIntent.COUNT
            plan.target_fields = []

        # Case 2: intent="count" but target_fields still has ["count"] or sort.field is "count"
        if plan.intent == AnalysisIntent.COUNT:
            plan.target_fields = [f for f in plan.target_fields if not _is_count_alias(f)]
            if plan.sort and _is_count_alias(plan.sort.field):
                plan.sort.field = "_count"  # normalize to derived column; preserve direction

        plan.target_fields = [self._remap_col(f, df) for f in plan.target_fields]
        if plan.group_by:
            plan.group_by = [self._remap_col(f, df) for f in plan.group_by]
        _COL_OPS = {"lt_col", "gt_col", "lte_col", "gte_col", "eq_col"}
        if plan.filters:
            for f in plan.filters:
                f.field = self._remap_col(f.field, df)
                if f.operator in _COL_OPS and isinstance(f.value, str):
                    f.value = self._remap_col(f.value, df)
        if plan.sort:
            plan.sort.field = self._remap_col(plan.sort.field, df)

    def _validate_columns(self, df: pd.DataFrame, plan: AnalysisPlan) -> None:
        # COUNT and DETAIL don't require target_fields
        no_target_intents = (AnalysisIntent.COUNT, AnalysisIntent.DETAIL)
        all_fields = set() if plan.intent in no_target_intents else set(plan.target_fields)
        if plan.group_by:
            all_fields.update(plan.group_by)
        _COL_OPS = {"lt_col", "gt_col", "lte_col", "gte_col", "eq_col"}
        if plan.filters:
            for f in plan.filters:
                all_fields.add(f.field)
                if f.operator in _COL_OPS and isinstance(f.value, str):
                    all_fields.add(f.value)
        # COUNT always sorts on the derived _count column, not a real column — skip sort validation
        if plan.sort and plan.intent != AnalysisIntent.COUNT:
            all_fields.add(plan.sort.field)

        missing = all_fields - set(df.columns)
        if missing:
            valid = ", ".join(sorted(df.columns))
            raise ValueError(
                f"Invalid column(s): {', '.join(sorted(missing))}. "
                f"Valid columns are: {valid}"
            )

        # Prevent groupby/target overlap which causes pandas "cannot insert X" error
        if plan.group_by and plan.intent in (
            AnalysisIntent.AGGREGATE, AnalysisIntent.TOP_N,
            AnalysisIntent.TREND, AnalysisIntent.COMPARISON, AnalysisIntent.DETAIL,
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
            # Column-to-column comparison operators (value is a column name)
            if f.operator == "lt_col" and str(f.value) in df.columns:
                df = df[df[f.field] < df[str(f.value)]]
            elif f.operator == "gt_col" and str(f.value) in df.columns:
                df = df[df[f.field] > df[str(f.value)]]
            elif f.operator == "lte_col" and str(f.value) in df.columns:
                df = df[df[f.field] <= df[str(f.value)]]
            elif f.operator == "gte_col" and str(f.value) in df.columns:
                df = df[df[f.field] >= df[str(f.value)]]
            elif f.operator == "eq_col" and str(f.value) in df.columns:
                df = df[df[f.field] == df[str(f.value)]]
            elif f.operator == "eq":
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
            # Coarsen dense date columns before grouping
            if len(plan.group_by) == 1:
                coarsened = self._coarsen_dates(df, plan.group_by[0], target, time_grain=plan.time_grain)
                if coarsened is not None:
                    return (ResultType.LIST, ListResult(items=coarsened))

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

    def _average(self, df: pd.DataFrame, plan: AnalysisPlan):
        target = plan.target_fields[0]
        if plan.group_by:
            grouped = df.groupby(plan.group_by)[target].mean().reset_index()
            if plan.sort:
                grouped = grouped.sort_values(
                    plan.sort.field, ascending=(plan.sort.direction == "asc")
                )
            if plan.limit:
                grouped = grouped.head(plan.limit)
            items = [
                {"label": str(row[plan.group_by[0]]), "value": round(self._serialize(row[target]), 2)}
                for _, row in grouped.iterrows()
            ]
            return (ResultType.LIST, ListResult(items=items))
        else:
            avg = round(self._serialize(df[target].mean()), 2)
            return (ResultType.SCALAR, ScalarResult(label=f"Average {target}", value=avg))

    def _count(self, df: pd.DataFrame, plan: AnalysisPlan):
        if plan.group_by:
            grouped = df.groupby(plan.group_by).size().reset_index(name="_count")
            if plan.sort:
                grouped = grouped.sort_values(
                    "_count", ascending=(plan.sort.direction == "asc")
                )
            else:
                grouped = grouped.sort_values("_count", ascending=False)
            if plan.limit:
                grouped = grouped.head(plan.limit)
            items = [
                {"label": str(row[plan.group_by[0]]), "value": int(row["_count"])}
                for _, row in grouped.iterrows()
            ]
            return (ResultType.LIST, ListResult(items=items))
        else:
            return (ResultType.SCALAR, ScalarResult(label="Total count", value=int(len(df))))

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

        # Coarsen dense date columns; honour explicit time_grain from the plan
        coarsened = self._coarsen_dates(df, group_col, target, time_grain=plan.time_grain)
        if coarsened is not None:
            return (ResultType.LIST, ListResult(items=coarsened))

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

        sort_dir = plan.sort.direction if plan.sort else "desc"
        grouped = grouped.sort_values(target, ascending=(sort_dir == "asc"))
        limit = plan.limit or 5
        grouped = grouped.head(limit)

        items = [
            {"label": str(row[group_col]), "value": self._serialize(row[target])}
            for _, row in grouped.iterrows()
        ]
        return (ResultType.LIST, ListResult(items=items))

    def _detail(self, df: pd.DataFrame, plan: AnalysisPlan):
        """
        Return individual rows (filtered) as a TabularResult.
        target_fields lists the columns to display; if empty, show all columns.
        Filters are already applied by the time this runs.
        """
        cols = plan.target_fields if plan.target_fields else list(df.columns)
        # Keep only columns that actually exist
        cols = [c for c in cols if c in df.columns]
        if not cols:
            cols = list(df.columns)

        if plan.sort:
            sort_col = plan.sort.field if plan.sort.field in df.columns else cols[0]
            df = df.sort_values(sort_col, ascending=(plan.sort.direction == "asc"))
        if plan.limit:
            df = df.head(plan.limit)

        rows = [
            [self._serialize(row[c]) for c in cols]
            for _, row in df[cols].iterrows()
        ]
        return (ResultType.TABULAR, TabularResult(columns=cols, rows=rows))

    def _correlation(self, df: pd.DataFrame, plan: AnalysisPlan):
        if len(plan.target_fields) < 2:
            raise ValueError("Correlation requires at least 2 target fields")
        f1, f2 = plan.target_fields[0], plan.target_fields[1]
        rows = [
            [self._serialize(row[f1]), self._serialize(row[f2])]
            for _, row in df[[f1, f2]].dropna().iterrows()
        ]
        return (ResultType.TABULAR, TabularResult(columns=[f1, f2], rows=rows))

    # Maps time_grain values to (resample_freq, date_format)
    _GRAIN_MAP: dict[str, tuple[str, str]] = {
        "day":     ("D",  "%b %d"),
        "week":    ("W",  "%b %d"),
        "month":   ("MS", "%b %Y"),
        "quarter": ("QS", "Q%q %Y"),
        "year":    ("YS", "%Y"),
    }

    def _coarsen_dates(
        self, df: pd.DataFrame, date_col: str, target: str,
        time_grain: str | None = None,
    ) -> list[dict] | None:
        """
        Resample a date column to a coarser period for readable charts.

        If time_grain is provided (from the user's explicit request), it takes
        priority. Otherwise auto-select based on the number of unique dates:
          ≤ 14   → no change (daily is fine)
          15-60  → weekly
          61-180 → monthly   ← was 14-day; monthly is almost always more useful
          > 180  → monthly
        """
        col = df[date_col]

        # Ensure datetime dtype; skip if column isn't date-like
        if not pd.api.types.is_datetime64_any_dtype(col):
            try:
                col = pd.to_datetime(col)
            except Exception:
                return None

        n_unique = int(col.nunique())

        if time_grain and time_grain in self._GRAIN_MAP:
            freq, fmt = self._GRAIN_MAP[time_grain]
        else:
            if n_unique <= 14:
                return None  # daily is already readable
            elif n_unique <= 60:
                freq, fmt = "W", "%b %d"
            else:
                freq, fmt = "MS", "%b %Y"  # monthly for anything denser

        try:
            tmp = df[[date_col, target]].copy()
            tmp[date_col] = col
            tmp = tmp.set_index(date_col).sort_index()
            resampled = (
                tmp[target]
                .resample(freq, closed="left", label="left")
                .sum()
                .dropna()
            )
            return [
                {"label": ts.strftime(fmt), "value": self._serialize(val)}
                for ts, val in resampled.items()
            ]
        except Exception:
            return None

    def _build_chart_data(self, result: tuple, plan: AnalysisPlan) -> ChartData:
        result_type, data = result
        labels = []
        datasets = []

        if isinstance(data, ListResult):
            labels = [item["label"] for item in data.items]
            series_label = plan.target_fields[0] if plan.target_fields else "Count"
            datasets = [
                {"label": series_label, "data": [item["value"] for item in data.items]}
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
