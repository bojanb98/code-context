from dataclasses import dataclass

from tree_sitter_language_pack import SupportedLanguage


@dataclass
class CodeChunk:
    content: str
    start_line: int
    end_line: int
    language: SupportedLanguage
    file_path: str
    doc: str | None = None
