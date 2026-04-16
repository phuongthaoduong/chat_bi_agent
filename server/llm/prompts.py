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
        numeric_cols = [c.name for c in p.columns if c.dtype in ("integer", "float")]
        categorical_cols = [c.name for c in p.columns if c.dtype in ("categorical", "text")]
        datetime_cols = [c.name for c in p.columns if c.dtype == "datetime"]
        cols = []
        for c in p.columns:
            role = "GROUP_BY candidate" if c.dtype in ("categorical", "text", "datetime") else "AGGREGATE candidate"
            col_desc = f"  - {c.name} ({c.dtype}) [{role}]: {c.unique_count} unique"
            if c.stats:
                col_desc += f", stats={c.stats}"
            if c.sample_values:
                # Show all sample values so LLM can identify what column holds e.g. East/West/South
                col_desc += f", ALL sample values={c.sample_values}"
            cols.append(col_desc)
        header = (
            f'Dataset: "{p.source.file_name}" / "{p.source.sheet_name}" ({p.row_count} rows)\n'
            f"  NUMERIC columns (use for target_fields to aggregate): {numeric_cols}\n"
            f"  CATEGORICAL/TEXT columns (use for group_by to slice data): {categorical_cols}\n"
            f"  DATETIME columns (use for group_by in trends): {datetime_cols}"
        )
        sections.append(header + "\n" + "\n".join(cols))
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
- For trend analysis, use datetime or ordered categorical columns for group_by
- CRITICAL: target_fields MUST be NUMERIC columns — they are the values to aggregate/sum
- CRITICAL: group_by MUST be CATEGORICAL or TEXT columns — they are the labels/dimensions
- CRITICAL: NEVER put the same column in both target_fields and group_by"""


CHAT_CLASSIFY_PROMPT = """You are a data analyst. Given the dataset schemas and the user's question, first classify the question, then produce an analysis plan if needed.

AVAILABLE DATASETS:
{dataset_inventory}

DETAILED SCHEMA:
{profile_detail}

CHAT HISTORY:
{chat_history}

USER QUESTION:
{question}

Respond with EXACTLY this JSON structure (no markdown, no code fences):
{{
  "question_type": "computational" or "conversational",
  "plan": {{
    "source": {{ "file_name": "...", "sheet_name": "..." }},
    "intent": "aggregate|distribution|trend|comparison|top_n|correlation",
    "target_fields": ["column_name"],
    "group_by": ["column_name"] or null,
    "filters": [{{"field": "...", "operator": "eq|ne|gt|lt|gte|lte|in|contains", "value": "..."}}] or null,
    "sort": {{"field": "...", "direction": "asc|desc"}} or null,
    "limit": number or null,
    "chart": {{
      "chart_type": "bar|line|pie|scatter",
      "title": "string",
      "x_axis": "column_name" or null,
      "y_axis": "column_name" or null
    }} or null
  }} or null
}}

RULES:
- Classify as "computational" if the question requires querying data (aggregations, filtering, ranking, comparisons, trends, proportions)
- Classify as "conversational" if the question is interpretive (explaining charts, summarizing patterns, asking "why", general advice)
- If "computational", plan MUST include a valid "source" and column references from the schema
- If "conversational", set plan to null
- Do NOT include any answer text
- CRITICAL: target_fields MUST be NUMERIC columns (integers or floats) — they are the values to aggregate/sum
- CRITICAL: group_by MUST be CATEGORICAL or TEXT columns — they are the labels/categories to slice by
- CRITICAL: NEVER put the same column in both target_fields and group_by
- CRITICAL: To identify which column is a region/category column, look at the sample values in the schema (e.g. a column with samples ["East","West","South"] is the region column)
- EXAMPLE "which product sold the most": target_fields=["sales_amount"], group_by=["product_name"], intent="top_n", chart_type="bar"
- EXAMPLE "which product has the most inventory": target_fields=["inventory_qty"], group_by=["product_name"], intent="top_n", chart_type="bar"
- EXAMPLE "proportion/percentage/share of revenue by region": target_fields=["revenue"], group_by=["region"], intent="aggregate", chart_type="pie"
- For proportion/percentage/share/breakdown questions, always use intent="aggregate" and chart_type="pie"
- If a question asks "which X has the most/least Y", X goes in group_by (categorical) and Y goes in target_fields (numeric)"""


CHAT_FORMAT_COMPUTATIONAL_PROMPT = """You are a data analyst assistant. The user asked a question and the system has computed the result. Write a clear, concise answer based on the actual data provided.

USER QUESTION:
{question}

COMPUTED RESULT:
{result_json}

RULES:
- Only state facts that appear in the computed result
- Do not invent or estimate numbers
- Keep the answer to 1-4 sentences
- Use natural language appropriate for a non-technical business user
- If the question asks for proportions, percentages, or shares: compute the total of all values, then express each item as a percentage of the total (e.g. "East: 45%, West: 30%, South: 25%")
- If the question asks for a ranking or top items: name the winner clearly first"""


CHAT_FORMAT_CONVERSATIONAL_PROMPT = """You are a data analyst assistant. The user asked an interpretive question. Answer based on the dataset context and conversation history provided.

AVAILABLE DATASETS:
{dataset_inventory}

DETAILED SCHEMA:
{profile_detail}

RECENT CHAT HISTORY (including prior computed results):
{chat_history}

USER QUESTION:
{question}

RULES:
- Base your answer on the dataset profile and prior computed results in chat history
- Do not invent specific numbers unless they appear in the provided context
- Clearly distinguish interpretation from established fact
- Keep the answer to 2-4 sentences
- Use natural language appropriate for a non-technical business user"""


def format_chat_history(messages: list) -> str:
    if not messages:
        return "(no prior messages)"
    lines = []
    for msg in messages[-10:]:  # last 10 messages for context window
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)
