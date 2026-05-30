from datetime import date
from dateutil.relativedelta import relativedelta


# ---------------------------------------------------------------------------
# Metric definitions: maps business terms → exact column + sheet
# ---------------------------------------------------------------------------
METRIC_DEFINITIONS = """METRICS (use the exact column name listed — never guess an alternative):
- 销售额 / 销售收入 / revenue / sales       → column "销售收入(元)"  in sheet "销售单"
- 成本 / cost / unit cost                  → column "成本(元)"       in sheet "销售单"
- 数量 / 销量 / quantity / units sold      → column "数量"           in sheet "销售单"
- 毛利润 / gross profit                    → column "毛利润(元)"     in sheet "利润汇总"
- 毛利率 / gross margin                    → column "毛利率"         in sheet "利润汇总"
- 月销售收入 / monthly revenue             → column "销售收入(元)"   in sheet "利润汇总"
- 商品 / product / item                   → column "商品名称"       in sheet "销售单"
- 客户 / customer                         → column "客户名称"       in sheet "销售单"
- 下单时间 / order date / date            → column "下单时间"       in sheet "销售单" """


# ---------------------------------------------------------------------------
# Ambiguous term rules: resolve vague qualitative terms to concrete metrics
# ---------------------------------------------------------------------------
AMBIGUOUS_TERM_RULES = """AMBIGUOUS TERM RULES (always apply these — never default to quantity):
- 卖得好 / best selling / top products / 销售最好  → rank by 销售收入(元), NOT 数量
- 利润高 / most profitable                        → rank by 毛利润(元)
- 毛利率高 / highest margin                       → rank by 毛利率
- 卖得最多 / most units / 数量最多                → rank by 数量
- 最受欢迎 / most popular                         → rank by 数量"""


# ---------------------------------------------------------------------------
# Join paths: how sheets relate to each other
# ---------------------------------------------------------------------------
JOIN_PATHS = """JOIN PATHS (use these when a question needs columns from multiple sheets):
- 销售单 vs 利润汇总: no direct join (different granularity — 销售单 is order-level, 利润汇总 is monthly)
- Always prefer 销售单 for order-level questions (individual transactions, filtering by date range)
- Always prefer 利润汇总 for monthly aggregated questions (monthly totals, 毛利率)"""


# ---------------------------------------------------------------------------
# Time expression builder (dynamic — based on today's date)
# ---------------------------------------------------------------------------
def _build_time_expressions(today: date) -> str:
    this_month_start = today.replace(day=1)
    next_month_start = this_month_start + relativedelta(months=1)
    last_month_start = this_month_start - relativedelta(months=1)
    this_year_start = today.replace(month=1, day=1)
    next_year_start = this_year_start.replace(year=today.year + 1)

    quarter = (today.month - 1) // 3
    quarter_start = today.replace(month=quarter * 3 + 1, day=1)
    next_quarter_start = quarter_start + relativedelta(months=3)
    last_quarter_start = quarter_start - relativedelta(months=3)

    return (
        f"TIME EXPRESSIONS (TODAY = {today.isoformat()} — use these exact date ranges, never guess):\n"
        f'- 本月 / this month     → gte "{this_month_start}" AND lt "{next_month_start}"\n'
        f'- 上月 / last month     → gte "{last_month_start}" AND lt "{this_month_start}"\n'
        f'- 本季度 / this quarter → gte "{quarter_start}" AND lt "{next_quarter_start}"\n'
        f'- 上季度 / last quarter → gte "{last_quarter_start}" AND lt "{quarter_start}"\n'
        f'- 今年 / this year      → gte "{this_year_start}" AND lt "{next_year_start}"\n'
        f'- 上年 / last year      → gte "{this_year_start.replace(year=today.year - 1)}" AND lt "{this_year_start}"'
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_semantic_context(today: date | None = None) -> str:
    if today is None:
        today = date.today()
    time_expr = _build_time_expressions(today)
    return (
        "SEMANTIC DEFINITIONS — follow these exactly, they override any guesses from column names:\n\n"
        + METRIC_DEFINITIONS + "\n\n"
        + time_expr + "\n\n"
        + AMBIGUOUS_TERM_RULES + "\n\n"
        + JOIN_PATHS
    )
