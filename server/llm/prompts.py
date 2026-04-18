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


DASHBOARD_SYSTEM_PROMPT = """You are a data analyst. Given the dataset schemas below, suggest exactly 1 joint chart that gives a business user the most useful overview of the data, plus 2-3 key insights.

AVAILABLE DATASETS:
{dataset_inventory}

DETAILED SCHEMA:
{profile_detail}

Respond with EXACTLY this JSON structure (no markdown, no code fences):
{{
  "insights": ["string — 1 sentence each, based on the stats provided"],
  "plan": {{
    "source": {{ "file_name": "...", "sheet_name": "..." }},
    "intent": "aggregate|average|count|detail|distribution|trend|comparison|top_n|correlation",
    "target_fields": ["column_name"],
    "group_by": ["column_name"] or null,
    "filters": null,
    "sort": {{"field": "...", "direction": "asc|desc"}} or null,
    "limit": number or null,
    "time_grain": "day|week|month|quarter|year" or null,
    "chart": {{
      "chart_type": "bar|line|pie|scatter",
      "title": "string",
      "x_axis": "column_name" or null,
      "y_axis": "column_name" or null
    }}
  }}
}}

RULES:
- Return exactly ONE plan that produces the single most informative chart
- Prefer a chart that combines multiple dimensions (e.g. grouped bar with multiple target_fields, or a comparison across categories)
- The plan MUST include a "chart" spec — this is the overview chart the user sees first
- The plan MUST include a "source" specifying which dataset to query
- Only reference columns that exist in the specified dataset's schema
- Only use intents from the allowed list: aggregate, average, count, distribution, trend, comparison, top_n, correlation
- Keep insights concise (1 sentence each), grounded in the stats provided
- For trend analysis, use datetime or ordered categorical columns for group_by
- TIME_GRAIN — set time_grain when the user specifies a time period for grouping date data:
  - "monthly", "by month", "each month", "month over month" → time_grain="month"
  - "weekly", "by week", "each week" → time_grain="week"
  - "daily", "by day", "each day" → time_grain="day"
  - "quarterly", "by quarter", "Q1/Q2/Q3/Q4" → time_grain="quarter"
  - "yearly", "annual", "by year" → time_grain="year"
  - If no time period is mentioned, set time_grain=null (engine will auto-select)
- EXAMPLE "monthly revenue trend" / "revenue by month": intent="trend", group_by=["date_col"], time_grain="month", chart_type="line"
- EXAMPLE "weekly sales": intent="trend", group_by=["date_col"], time_grain="week", chart_type="line"
- CRITICAL: target_fields MUST be NUMERIC columns — they are the values to aggregate/sum
- CRITICAL: group_by MUST be CATEGORICAL or TEXT columns — they are the labels/dimensions
- CRITICAL: NEVER put the same column in both target_fields and group_by
- COUNT INTENT: Use intent="count" with target_fields=[] (empty) when counting rows. group_by is optional for "count by category" questions."""


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
  "question_type": "computational" or "conversational" or "irrelevant",
  "plan": {{
    "source": {{ "file_name": "...", "sheet_name": "..." }},
    "join": {{
      "sheet_name": "...",
      "on": "column_name_present_in_both_sheets",
      "columns": ["column_to_bring_in"]
    }} or null,
    "intent": "aggregate|average|count|detail|distribution|trend|comparison|top_n|correlation",
    "target_fields": ["column_name"],
    "group_by": ["column_name"] or null,
    "filters": [{{"field": "...", "operator": "eq|ne|gt|lt|gte|lte|in|contains|lt_col|gt_col|lte_col|gte_col|eq_col", "value": "..."}}] or null,
    "time_grain": "day|week|month|quarter|year" or null,
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
- Classify as "computational" if the question requires querying data (aggregations, filtering, ranking, comparisons, trends, proportions, counts)
- Classify as "conversational" if the question is interpretive (explaining charts, summarizing patterns, asking "why", general advice about the data)
- Classify as "irrelevant" ONLY if the question is completely unrelated to data analysis or the uploaded datasets (e.g., jokes, recipes, general knowledge, coding help, personal advice, weather, politics, creative writing). When in doubt, classify as "computational" or "conversational" — never classify a question as "irrelevant" if it could plausibly relate to the uploaded data.
- If "computational", plan MUST include a valid "source" and column references from the schema
- If "conversational", set plan to null
- If "irrelevant", set plan to null
- Do NOT include any answer text
- CRITICAL: target_fields MUST be NUMERIC columns (integers or floats) — they are the values to aggregate/sum. EXCEPTION: for intent="count", target_fields MUST be [] (empty array). EXCEPTION: for intent="detail", target_fields is the list of columns to DISPLAY (any type), or [] to show all columns.
- CRITICAL: NEVER use "count" as a column name in target_fields — "count" is a derived aggregation result, not a column. Use intent="count" with target_fields=[] instead.
- CRITICAL: group_by MUST be CATEGORICAL or TEXT columns — they are the labels/categories to slice by
- CRITICAL: NEVER put the same column in both target_fields and group_by
- CRITICAL: To identify which column is a region/category column, look at the sample values in the schema (e.g. a column with samples ["East","West","South"] is the region column)
- AGGREGATION RULE — for questions about frequency, ranking, or totals always use aggregation with group_by:
  - Frequency ("how often", "how many times", "number of X per Y") → intent="count", target_fields=[], group_by=["Y_col"]
  - Totals by dimension ("total revenue by product", "sum of X per category") → intent="aggregate", target_fields=["numeric_col"], group_by=["category_col"]
  - Ranking ("top N", "most", "least", "highest", "lowest") → intent="top_n", target_fields=["numeric_col"], group_by=["category_col"]
  - Average / mean ("average order value", "mean price", "avg revenue per salesperson") → intent="average", target_fields=["numeric_col"], group_by=["category_col"]
- COUNT INTENT — use intent="count" with target_fields=[] when the question asks "how many X", "number of X", "count of X", or any row-counting question. Do NOT use a column name in target_fields for count.
- EXAMPLE "how many orders": intent="count", target_fields=[], group_by=null, chart=null
- EXAMPLE "how many orders by region": intent="count", target_fields=[], group_by=["region_col"], chart_type="bar"
- EXAMPLE "how many orders this month": intent="count", target_fields=[], filters=[{{date filter}}], group_by=null, chart=null
- EXAMPLE "who has the most orders / which salesperson has the most orders / most number of orders": intent="count", target_fields=[], group_by=["salesperson_col"], limit=1, chart=null (row count per person — never put "count" in target_fields)
- EXAMPLE "order count by salesperson / number of orders per customer": intent="count", target_fields=[], group_by=["salesperson_col"], chart_type="bar"
- EXAMPLE "which product sold the most": target_fields=["sales_amount"], group_by=["product_name"], intent="top_n", limit=1, chart=null (single winner, no chart)
- EXAMPLE "top 5 products by sales": target_fields=["sales_amount"], group_by=["product_name"], intent="top_n", limit=5, chart_type="bar" (ranking list, chart helps)
- EXAMPLE "which product has the most inventory": target_fields=["inventory_qty"], group_by=["product_name"], intent="top_n", limit=1, chart=null (single winner, no chart)
- EXAMPLE "total revenue": target_fields=["revenue"], group_by=null, intent="aggregate", chart=null (scalar, no chart)
- EXAMPLE "average order value per salesperson / mean revenue by region": target_fields=["revenue_col"], group_by=["salesperson_col"], intent="average", chart_type="bar"
- EXAMPLE "what is the average price": target_fields=["price_col"], group_by=null, intent="average", chart=null (scalar)
- EXAMPLE "proportion/percentage/share of revenue by region": target_fields=["revenue"], group_by=["region"], intent="aggregate", chart_type="pie"
- For proportion/percentage/share/breakdown questions, always use intent="aggregate" and chart_type="pie"
- If a question asks "which X has the most/least Y", X goes in group_by (categorical) and Y goes in target_fields (numeric)
- If a question uses "who" but the dataset has no person/salesperson/employee column, use the best available categorical column (e.g. product, region) but set intent accordingly so the format step can clarify the mismatch to the user
- DETAIL INTENT — use intent="detail" when the question asks to LIST or SHOW INDIVIDUAL ROWS (not aggregated results):
  - "which orders were sold below cost" → detail intent with column-to-column filter
  - "list all products with inventory < 10" → detail intent with numeric filter
  - "show me all transactions where profit is negative" → detail intent
  - "which customers haven't placed an order" → detail intent
  - For detail, target_fields = the columns to display (e.g. ["Order_ID", "Sale_Price", "Cost", "Salesperson"]); use [] to show all columns
  - group_by is NOT used for detail intent (we return individual rows, not grouped aggregates)
  - COLUMN-TO-COLUMN FILTERS: when comparing one column against another column (not a fixed number), use _col operators:
    - "sale_price < wholesale_cost" → {{"field": "Sale_Price", "operator": "lt_col", "value": "Wholesale_Cost"}}
    - "revenue > target" → {{"field": "Revenue", "operator": "gt_col", "value": "Target"}}
    - "actual_cost <= budget" → {{"field": "Actual_Cost", "operator": "lte_col", "value": "Budget"}}
  - EXAMPLE "which orders were sold below wholesale cost, who sold them": intent="detail", target_fields=["Order_ID","Sale_Price","Wholesale_Cost","Salesperson"], filters=[{{"field":"Sale_Price","operator":"lt_col","value":"Wholesale_Cost"}}], chart=null
  - EXAMPLE "list all overdue invoices": intent="detail", target_fields=[], filters=[{{"field":"Status","operator":"eq","value":"overdue"}}], chart=null
- JOIN RULE — use "join" in the plan when the question requires a column that exists in a DIFFERENT sheet from the primary source:
  - The primary "source" sheet is the one that has the main rows (e.g. "Sales Order" for order-level questions)
  - "join.sheet_name" is the sheet that has the extra column needed (e.g. "Purchase Orders" for cost data)
  - "join.on" MUST be a column name that appears in BOTH the source sheet and the join sheet (e.g. "Product ID")
  - "join.columns" lists only the column(s) you need from the join sheet (e.g. ["Unit Cost (¥)"])
  - After joining, the joined columns are available in filters, target_fields, and sort — use them normally
  - EXAMPLE "which orders were sold below wholesale cost, who sold them":
      source={{"sheet_name": "Sales Order"}},
      join={{"sheet_name": "Purchase Orders", "on": "Product ID", "columns": ["Unit Cost (¥)"]}},
      intent="detail",
      target_fields=["Order ID", "Unit Price (¥)", "Unit Cost (¥)", "Salesperson"],
      filters=[{{"field": "Unit Price (¥)", "operator": "lt_col", "value": "Unit Cost (¥)"}}],
      chart=null
  - EXAMPLE "average profit margin by product" (where cost is in Purchase Orders):
      source={{"sheet_name": "Sales Order"}},
      join={{"sheet_name": "Purchase Orders", "on": "Product ID", "columns": ["Unit Cost (¥)"]}},
      intent="average",
      target_fields=["Unit Price (¥)"],
      group_by=["Product Name"],
      chart_type="bar"
  - Do NOT use join if all needed columns are already in the same sheet
  - Do NOT join more than one extra sheet per plan
- CHART SUPPRESSION — set chart to null when visualization adds NO value:
  - Single-winner questions ("who sells the most", "which product has the highest revenue", "what is the top X") → set limit=1 AND chart=null; the answer is one sentence
  - Pure scalar aggregations with no group_by ("total revenue", "average price", "how many rows", "how many orders") → chart=null; the answer is a single number
  - Yes/no or existence questions → chart=null
- CHART GENERATION — only include a chart spec when visualization genuinely helps:
  - Multiple categories being compared (e.g., "sales by region", "revenue per product") → bar or pie chart
  - Time-based trends ("sales over months", "monthly revenue") → line chart
  - Top N where N > 1 and the question implies a ranking/list view ("top 5 products", "show me the best sellers") → bar chart
  - Distributions or breakdowns ("proportion of sales by channel", "share by category") → pie chart"""


CHAT_FORMAT_COMPUTATIONAL_PROMPT = """You are a data analyst assistant. The user asked a question and the system has computed the result. Write a clear, concise answer based on the actual data provided.

USER QUESTION:
{question}

COMPUTED RESULT:
{result_json}

RULES:
- Only state facts that appear in the computed result
- Do not invent or estimate numbers
- Use natural language appropriate for a non-technical business user
- If the result type is "table" (individual rows): present ALL rows as a markdown table — do NOT summarize into 1-4 sentences. Include every row from the result. Add a one-sentence intro stating how many rows were found (e.g. "Found 12 orders sold below wholesale cost:"), then the full table.
- If the result type is "list" or "scalar": keep the answer to 1-4 sentences
- If the question asks for proportions, percentages, or shares: compute the total of all values, then express each item as a percentage of the total (e.g. "East: 45%, West: 30%, South: 25%")
- If the question asks for a ranking or top items: name the winner clearly first
- SEMANTIC MISMATCH: If the question uses "who" or implies a person/individual/salesperson but the result contains product names, region names, channel names, or other non-person entities: explicitly clarify what the result dimension actually represents. For example: "The data doesn't track individual salespeople. By product, Hammer leads with 720 units sold." Never refer to a product, region, or category as if it were a person.
- Always look at what the result's grouping dimension actually represents (e.g. product vs. person vs. region) and make sure your answer accurately labels it"""


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
