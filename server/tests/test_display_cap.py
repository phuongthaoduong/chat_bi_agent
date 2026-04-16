from models.domain import ListResult, TabularResult

DISPLAY_CAP = 10_000


def test_tabular_result_within_cap():
    rows = [[i, f"item_{i}"] for i in range(100)]
    result = TabularResult(columns=["id", "name"], rows=rows)

    capped_rows = result.rows[:DISPLAY_CAP]
    assert len(capped_rows) == 100
    assert len(capped_rows) == len(result.rows)


def test_tabular_result_exceeds_cap():
    rows = [[i, f"item_{i}"] for i in range(15_000)]
    result = TabularResult(columns=["id", "name"], rows=rows)

    total = len(result.rows)
    capped_rows = result.rows[:DISPLAY_CAP]

    assert total == 15_000
    assert len(capped_rows) == DISPLAY_CAP


def test_list_result_not_capped():
    """List results (aggregations) are never capped — they're already summarized."""
    items = [{"label": f"item_{i}", "value": i} for i in range(50)]
    result = ListResult(items=items)
    assert len(result.items) == 50
