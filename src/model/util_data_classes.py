from dataclasses import dataclass

from langchain_core.documents import Document


@dataclass
class AnalyzedFileDefinition:
    doc: Document
    analysis: str
    name: str
    relative_path: str
    file_extension: str
