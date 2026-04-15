import csv
from io import BytesIO, StringIO
import chardet
import pandas as pd
from models.domain import ParsedFile, SheetData
from parsers.base import BaseParser

class CsvParser(BaseParser):
    def parse(self, filename: str, content: BytesIO) -> ParsedFile:
        raw = content.read()
        if not raw.strip():
            raise ValueError(f"File is empty: {filename}")
        encoding = chardet.detect(raw)["encoding"] or "utf-8"
        text = raw.decode(encoding)
        dialect = csv.Sniffer().sniff(text[:8192])
        df = pd.read_csv(StringIO(text), sep=dialect.delimiter)
        if df.empty:
            raise ValueError(f"File is empty: {filename}")
        sheet = SheetData(name="Sheet1", df=df)
        return ParsedFile(name=filename, sheets=[sheet])
