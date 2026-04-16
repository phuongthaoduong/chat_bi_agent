import pandas as pd
from models.domain import DataSource, SheetData
from profiler.profiler import DataProfiler

def test_profile_numeric_column():
    df = pd.DataFrame({"sales": [100, 200, 300, 400, 500]})
    sheet = SheetData(name="Sheet1", df=df)
    source = DataSource(file_name="test.csv", sheet_name="Sheet1")
    profiler = DataProfiler()
    profile = profiler.profile(sheet, source)
    assert profile.row_count == 5
    assert profile.column_count == 1
    assert profile.source == source
    col = profile.columns[0]
    assert col.name == "sales"
    assert col.dtype == "numeric"
    assert col.null_count == 0
    assert col.null_pct == 0.0
    assert col.unique_count == 5
    assert col.stats["min"] == 100
    assert col.stats["max"] == 500
    assert col.stats["mean"] == 300.0

def test_profile_categorical_column():
    df = pd.DataFrame({"color": ["red", "blue", "red", "green", "blue"]})
    sheet = SheetData(name="Sheet1", df=df)
    source = DataSource(file_name="test.csv", sheet_name="Sheet1")
    profiler = DataProfiler()
    profile = profiler.profile(sheet, source)
    col = profile.columns[0]
    assert col.dtype == "categorical"
    assert col.unique_count == 3
    assert "top_values" in col.stats

def test_profile_datetime_column():
    df = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"])})
    sheet = SheetData(name="Sheet1", df=df)
    source = DataSource(file_name="test.csv", sheet_name="Sheet1")
    profiler = DataProfiler()
    profile = profiler.profile(sheet, source)
    col = profile.columns[0]
    assert col.dtype == "datetime"
    assert "min" in col.stats
    assert "max" in col.stats

def test_profile_with_nulls():
    df = pd.DataFrame({"value": [1.0, None, 3.0, None, 5.0]})
    sheet = SheetData(name="Sheet1", df=df)
    source = DataSource(file_name="test.csv", sheet_name="Sheet1")
    profiler = DataProfiler()
    profile = profiler.profile(sheet, source)
    col = profile.columns[0]
    assert col.null_count == 2
    assert col.null_pct == 40.0

def test_profile_sample_values():
    df = pd.DataFrame({"name": ["Alice", "Bob", "Carol", "Dave", "Eve"]})
    sheet = SheetData(name="Sheet1", df=df)
    source = DataSource(file_name="test.csv", sheet_name="Sheet1")
    profiler = DataProfiler()
    profile = profiler.profile(sheet, source)
    col = profile.columns[0]
    assert len(col.sample_values) <= 5
    assert all(isinstance(v, str) for v in col.sample_values)
