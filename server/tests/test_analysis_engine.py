import pandas as pd
import pytest

from analysis.engine import AnalysisEngine
from models.domain import (
    AnalysisIntent,
    AnalysisPlan,
    ChartSpec,
    DataSource,
    FilterCondition,
    JoinSpec,
    ResultType,
    SheetData,
    SortSpec,
)

SOURCE = DataSource(file_name="test.csv", sheet_name="Sheet1")


def _make_sales_data() -> list[SheetData]:
    df = pd.DataFrame(
        {
            "month": ["Jan", "Feb", "Mar", "Jan", "Feb", "Mar"],
            "product": ["A", "A", "A", "B", "B", "B"],
            "sales": [100, 150, 200, 80, 120, 160],
            "region": ["North", "North", "South", "South", "North", "South"],
        }
    )
    return [SheetData(name="Sheet1", df=df)]


def test_aggregate_sum():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["sales"],
        group_by=["product"],
    )
    result = engine.execute_plan(plan, _make_sales_data())
    assert result.result_type == ResultType.LIST
    items = result.data.items
    assert len(items) == 2
    product_a = next(i for i in items if i["label"] == "A")
    assert product_a["value"] == 450


def test_top_n():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.TOP_N,
        target_fields=["sales"],
        group_by=["month"],
        sort=SortSpec(field="sales", direction="desc"),
        limit=2,
    )
    result = engine.execute_plan(plan, _make_sales_data())
    assert result.result_type == ResultType.LIST
    assert len(result.data.items) == 2
    assert result.data.items[0]["label"] == "Mar"


def test_distribution():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.DISTRIBUTION,
        target_fields=["region"],
    )
    result = engine.execute_plan(plan, _make_sales_data())
    assert result.result_type == ResultType.LIST
    items = result.data.items
    assert any(i["label"] == "North" for i in items)


def test_filter():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["sales"],
        group_by=["product"],
        filters=[FilterCondition(field="region", operator="eq", value="North")],
    )
    result = engine.execute_plan(plan, _make_sales_data())
    items = result.data.items
    product_a = next(i for i in items if i["label"] == "A")
    assert product_a["value"] == 250  # Jan(100) + Feb(150)


def test_chart_data_generated():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["sales"],
        group_by=["product"],
        chart=ChartSpec(chart_type="bar", title="Sales by Product"),
    )
    result = engine.execute_plan(plan, _make_sales_data())
    assert result.chart_data is not None
    assert result.chart_data.chart_type == "bar"
    assert result.chart_data.title == "Sales by Product"
    assert len(result.chart_data.labels) == 2


def test_invalid_source_raises():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=DataSource(file_name="missing.csv", sheet_name="NonExistentSheet"),
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["sales"],
    )
    with pytest.raises(ValueError, match="not found"):
        engine.execute_plan(plan, _make_sales_data())


def test_invalid_column_raises():
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["nonexistent"],
    )
    with pytest.raises(ValueError, match="column"):
        engine.execute_plan(plan, _make_sales_data())


def test_join_spec_exists():
    j = JoinSpec(sheet_name="Purchase Orders", on="Product ID", columns=["Unit Cost (¥)"])
    assert j.sheet_name == "Purchase Orders"
    assert j.on == "Product ID"
    assert j.columns == ["Unit Cost (¥)"]


def test_analysis_plan_has_join_field():
    plan = AnalysisPlan(
        source=SOURCE,
        intent=AnalysisIntent.AGGREGATE,
        target_fields=["sales"],
        join=JoinSpec(sheet_name="Other", on="id", columns=["cost"]),
    )
    assert plan.join is not None
    assert plan.join.sheet_name == "Other"


def _make_join_sheets() -> list[SheetData]:
    """Sales orders + a separate Purchase Orders sheet with unit cost."""
    sales_df = pd.DataFrame({
        "Order ID": ["ORD-001", "ORD-002", "ORD-003"],
        "Product ID": ["P1", "P2", "P1"],
        "Unit Price (¥)": [100, 50, 80],
        "Salesperson": ["Alice", "Bob", "Alice"],
    })
    cost_df = pd.DataFrame({
        "Product ID": ["P1", "P2"],
        "Unit Cost (¥)": [90, 60],
    })
    return [
        SheetData(name="Sales Order", df=sales_df),
        SheetData(name="Purchase Orders", df=cost_df),
    ]


def test_join_brings_in_cost_column():
    """After join, merged df should contain Unit Cost (¥)."""
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=DataSource(file_name="test.csv", sheet_name="Sales Order"),
        intent=AnalysisIntent.DETAIL,
        target_fields=["Order ID", "Unit Price (¥)", "Unit Cost (¥)", "Salesperson"],
        join=JoinSpec(
            sheet_name="Purchase Orders",
            on="Product ID",
            columns=["Unit Cost (¥)"],
        ),
    )
    result = engine.execute_plan(plan, _make_join_sheets())
    assert result.result_type == ResultType.TABULAR
    assert "Unit Cost (¥)" in result.data.columns


def test_join_filter_below_cost():
    """Orders where Unit Price < Unit Cost should be ORD-002 only."""
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=DataSource(file_name="test.csv", sheet_name="Sales Order"),
        intent=AnalysisIntent.DETAIL,
        target_fields=["Order ID", "Unit Price (¥)", "Unit Cost (¥)", "Salesperson"],
        filters=[FilterCondition(field="Unit Price (¥)", operator="lt_col", value="Unit Cost (¥)")],
        join=JoinSpec(
            sheet_name="Purchase Orders",
            on="Product ID",
            columns=["Unit Cost (¥)"],
        ),
    )
    result = engine.execute_plan(plan, _make_join_sheets())
    assert result.result_type == ResultType.TABULAR
    order_ids = [row[result.data.columns.index("Order ID")] for row in result.data.rows]
    assert order_ids == ["ORD-002", "ORD-003"]


def test_join_missing_sheet_raises():
    """Referencing a non-existent join sheet should raise ValueError."""
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=DataSource(file_name="test.csv", sheet_name="Sales Order"),
        intent=AnalysisIntent.DETAIL,
        target_fields=[],
        join=JoinSpec(sheet_name="Nonexistent", on="Product ID", columns=["cost"]),
    )
    with pytest.raises(ValueError, match="Join sheet not found"):
        engine.execute_plan(plan, _make_join_sheets())


def test_join_key_fuzzy_match():
    """Join key 'product_id' in plan should match 'Product ID' column in both sheets."""
    engine = AnalysisEngine()
    plan = AnalysisPlan(
        source=DataSource(file_name="test.csv", sheet_name="Sales Order"),
        intent=AnalysisIntent.DETAIL,
        target_fields=[],
        join=JoinSpec(
            sheet_name="Purchase Orders",
            on="product_id",   # <- lowercase/underscore variant
            columns=["unit_cost_(¥)"],  # <- also fuzzy
        ),
    )
    result = engine.execute_plan(plan, _make_join_sheets())
    assert "Unit Cost (¥)" in result.data.columns
