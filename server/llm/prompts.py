from models.domain import SheetProfile


def build_dataset_inventory(profiles: list[SheetProfile]) -> str:
    lines = []
    for p in profiles:
        col_info = ", ".join(f"{c.name} ({c.dtype})" for c in p.columns)
        lines.append(
            f'- "{p.source.file_name}" / "{p.source.sheet_name}": '
            f"columns [{col_info}] ({p.row_count} rows)"
        )
    return "\n".join(lines)


def build_profile_detail(profiles: list[SheetProfile]) -> str:
    sections = []
    for p in profiles:
        cols = []
        for c in p.columns:
            col_desc = f"  - {c.name} ({c.dtype}): {c.unique_count} unique"
            if c.stats:
                col_desc += f", stats={c.stats}"
            if c.sample_values:
                col_desc += f", samples={c.sample_values[:3]}"
            cols.append(col_desc)
        sections.append(
            f'Dataset: "{p.source.file_name}" / "{p.source.sheet_name}" '
            f"({p.row_count} rows)\n" + "\n".join(cols)
        )
    return "\n\n".join(sections)


DASHBOARD_SYSTEM_PROMPT = """You are a data analyst. Given the dataset schemas below, suggest 3-5 charts that give a business user the most useful overview.

AVAILABLE DATASETS:
{dataset_inventory}

DETAILED SCHEMA:
{profile_detail}

Respond with EXACTLY this JSON structure (no markdown, no code fences):
{{
  "insights": ["string — 1 sentence each, based on the stats provided"],
  "plans": [
    {{
      "source": {{ "file_name": "...", "sheet_name": "..." }},
      "intent": "aggregate|distribution|trend|comparison|top_n|correlation",
      "target_fields": ["column_name"],
      "group_by": ["column_name"] or null,
      "filters": null,
      "sort": {{"field": "...", "direction": "asc|desc"}} or null,
      "limit": number or null,
      "chart": {{
        "chart_type": "bar|line|pie|scatter",
        "title": "string",
        "x_axis": "column_name" or null,
        "y_axis": "column_name" or null
      }}
    }}
  ]
}}

RULES:
- Every plan MUST include a "source" specifying which dataset to query
- Only reference columns that exist in the specified dataset's schema
- Only use intents from the allowed list: aggregate, distribution, trend, comparison, top_n, correlation
- Keep insights concise (1 sentence each), grounded in the stats provided
- Suggest charts that highlight different aspects of the data
- For trend analysis, use datetime or ordered categorical columns for group_by"""
