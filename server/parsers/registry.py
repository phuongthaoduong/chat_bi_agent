from pathlib import Path
from parsers.base import BaseParser
from parsers.csv_parser import CsvParser
from parsers.xlsx_parser import XlsxParser
from parsers.xls_parser import XlsParser

_PARSERS: dict[str, type[BaseParser]] = {
    ".csv": CsvParser,
    ".xlsx": XlsxParser,
    ".xls": XlsParser,
}

def get_parser(filename: str) -> BaseParser:
    ext = Path(filename).suffix.lower()
    parser_class = _PARSERS.get(ext)
    if parser_class is None:
        raise ValueError(
            f"Unsupported file format: {ext}. "
            f"Supported formats: {', '.join(sorted(_PARSERS.keys()))}"
        )
    return parser_class()
