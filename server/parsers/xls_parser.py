from io import BytesIO
import pandas as pd
from models.domain import ParsedFile, SheetData
from parsers.base import BaseParser

class XlsParser(BaseParser):
    def parse(self, filename: str, content: BytesIO) -> ParsedFile:
        try:
            xls = pd.ExcelFile(content, engine="xlrd")
        except Exception:
            content.seek(0)
            xls = pd.ExcelFile(content, engine="openpyxl")
        sheets: list[SheetData] = []
        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name)
            if not df.empty:
                sheets.append(SheetData(name=sheet_name, df=df))
        if not sheets:
            raise ValueError(f"File has no data: {filename}")
        return ParsedFile(name=filename, sheets=sheets)
