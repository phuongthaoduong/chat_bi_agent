from io import BytesIO
import pandas as pd
import pytest
from parsers.xlsx_parser import XlsxParser

def _make_xlsx(sheets: dict[str, pd.DataFrame]) -> BytesIO:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    buf.seek(0)
    return buf

def test_xlsx_single_sheet():
    df = pd.DataFrame({"product": ["A", "B"], "sales": [100, 200]})
    content = _make_xlsx({"Sheet1": df})
    parser = XlsxParser()
    result = parser.parse("test.xlsx", content)
    assert result.name == "test.xlsx"
    assert len(result.sheets) == 1
    assert result.sheets[0].name == "Sheet1"
    assert len(result.sheets[0].df) == 2
    assert list(result.sheets[0].df.columns) == ["product", "sales"]

def test_xlsx_multiple_sheets():
    sheets = {
        "Sales": pd.DataFrame({"month": ["Jan"], "revenue": [1000]}),
        "Inventory": pd.DataFrame({"item": ["Widget"], "stock": [50]}),
    }
    content = _make_xlsx(sheets)
    parser = XlsxParser()
    result = parser.parse("multi.xlsx", content)
    assert len(result.sheets) == 2
    assert result.sheets[0].name == "Sales"
    assert result.sheets[1].name == "Inventory"

def test_xlsx_empty_sheet_raises():
    df = pd.DataFrame()
    content = _make_xlsx({"Empty": df})
    parser = XlsxParser()
    with pytest.raises(ValueError, match="no data"):
        parser.parse("empty.xlsx", content)
