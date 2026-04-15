from io import BytesIO
from pathlib import Path
import pytest
from parsers.csv_parser import CsvParser

FIXTURES = Path(__file__).parent / "fixtures"

def test_csv_parser_reads_file():
    content = (FIXTURES / "sample.csv").read_bytes()
    parser = CsvParser()
    result = parser.parse("sample.csv", BytesIO(content))
    assert result.name == "sample.csv"
    assert len(result.sheets) == 1
    assert result.sheets[0].name == "Sheet1"
    assert len(result.sheets[0].df) == 5
    assert list(result.sheets[0].df.columns) == ["date", "product", "amount", "region"]

def test_csv_parser_detects_semicolon_delimiter():
    csv_content = b"name;age;city\nAlice;30;NYC\nBob;25;LA"
    parser = CsvParser()
    result = parser.parse("semicolon.csv", BytesIO(csv_content))
    assert len(result.sheets[0].df) == 2
    assert list(result.sheets[0].df.columns) == ["name", "age", "city"]

def test_csv_parser_handles_empty_file():
    parser = CsvParser()
    with pytest.raises(ValueError, match="empty"):
        parser.parse("empty.csv", BytesIO(b""))
