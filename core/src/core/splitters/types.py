from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node
from tree_sitter_language_pack import SupportedLanguage


@dataclass
class CodeChunk:
    id: str
    content: str
    start_line: int
    end_line: int
    language: SupportedLanguage
    file_path: Path
    doc: str | None = None
    node: Node | None = None
    parent_chunk_id: str | None = None
