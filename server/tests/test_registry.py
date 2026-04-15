import pytest
from parsers.registry import get_parser
from parsers.csv_parser import CsvParser
from parsers.xlsx_parser import XlsxParser
from parsers.xls_parser import XlsParser

def test_csv_extension():
    assert isinstance(get_parser("data.csv"), CsvParser)

def test_xlsx_extension():
    assert isinstance(get_parser("report.xlsx"), XlsxParser)

def test_xls_extension():
    assert isinstance(get_parser("old_report.xls"), XlsParser)

def test_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported"):
        get_parser("document.pdf")

def test_case_insensitive():
    assert isinstance(get_parser("DATA.CSV"), CsvParser)
    assert isinstance(get_parser("Report.XLSX"), XlsxParser)
