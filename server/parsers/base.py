from abc import ABC, abstractmethod
from io import BytesIO
from models.domain import ParsedFile

class BaseParser(ABC):
    @abstractmethod
    def parse(self, filename: str, content: BytesIO) -> ParsedFile:
        ...
