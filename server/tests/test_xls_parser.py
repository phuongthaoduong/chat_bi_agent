from io import BytesIO
import pandas as pd
import pytest
from parsers.xls_parser import XlsParser

def test_xls_parser_reads_file():
    df = pd.DataFrame({"name": ["Alice", "Bob"], "score": [95, 87]})
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    parser = XlsParser()
    result = parser.parse("test.xls", buf)
    assert result.name == "test.xls"
    assert len(result.sheets) >= 1
    assert len(result.sheets[0].df) == 2

def test_xls_parser_empty_raises():
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame().to_excel(writer, index=False)
    buf.seek(0)
    parser = XlsParser()
    with pytest.raises(ValueError, match="no data"):
        parser.parse("empty.xls", buf)
