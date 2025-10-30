from pathlib import Path

from loguru import logger
from tree_sitter import Node, Parser
from tree_sitter_language_pack import SupportedLanguage, get_parser

from .base import BaseSplitter
from .types import CodeChunk
from .utils import LANGUAGE_EXTENSIONS, SPLITTABLE_NODE_TYPES


class TreeSitterSplitter(BaseSplitter):
    """Tree-sitter based code splitter with fallback to text splitting."""

    def __init__(self, chunk_size: int = 2500, chunk_overlap: int = 300) -> None:
        """Initialize tree-sitter splitter.

        Args:
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap size in characters
        """
        super().__init__(chunk_size, chunk_overlap)
        self._parsers: dict[SupportedLanguage, Parser] = {}

    def _get_parser(self, lang: SupportedLanguage) -> Parser | None:
        if lang in self._parsers:
            return self._parsers[lang]

        try:
            parser = get_parser(lang)
            self._parsers[lang] = parser
            logger.debug("Loaded tree-sitter parser for {}", lang)
            return parser

        except Exception as e:
            logger.warning("Failed to load tree-sitter parser for %s: %s", lang, e)
            return None

    async def split(self, code: str, file_path: Path) -> list[CodeChunk]:
        """Split code into chunks using tree-sitter.

        Args:
            code: Code content to split
            language: Programming language
            file_path: Path to the file

        Returns:
            List of code chunks
        """

        lang = LANGUAGE_EXTENSIONS.get(file_path.suffix)

        if lang is None:
            logger.debug("File type not supported by Tree Sitter %s", file_path.suffix)
            return await self._fallback_text_split(code, file_path)

        parser = self._get_parser(lang)
        if not parser:
            return await self._fallback_text_split(code, file_path)

        try:
            tree = parser.parse(bytes(code, "utf-8"))

            if not tree.root_node:
                logger.warning("Failed to parse AST for %s", file_path.name)
                return await self._fallback_text_split(code, file_path)

            chunks = self._extract_chunks(tree.root_node, lang, code, file_path)

            refined_chunks = await self._refine_chunks(chunks)

            return refined_chunks

        except Exception as e:
            logger.warning("Tree Sitter failed for %s %s", file_path.name, e)
            return await self._fallback_text_split(code, file_path)

    def _extract_chunks(
        self,
        node: Node,
        lang: SupportedLanguage,
        code: str,
        file_path: Path,
    ) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []
        splittable_types = SPLITTABLE_NODE_TYPES.get(lang)

        if splittable_types is None or len(splittable_types) == 0:
            raise RuntimeError("Invalid splittable types for %s", lang)

        def traverse(current_node: Node) -> None:
            """Recursively traverse AST nodes."""
            if current_node.type in splittable_types:
                start_line = current_node.start_point[0] + 1
                end_line = current_node.end_point[0] + 1

                start_byte = current_node.start_byte
                end_byte = current_node.end_byte
                node_text = code.encode("utf-8")[start_byte:end_byte].decode("utf-8")

                if node_text.strip():
                    chunks.append(
                        CodeChunk(
                            content=node_text,
                            start_line=start_line,
                            end_line=end_line,
                            language=lang,
                            file_path=str(file_path),
                        )
                    )

            for child in current_node.children:
                traverse(child)

        traverse(node)

        if not chunks:
            lines = code.split("\n")
            chunks.append(
                CodeChunk(
                    content=code,
                    start_line=1,
                    end_line=len(lines),
                    language=lang,
                    file_path=str(file_path),
                )
            )

        return chunks

    async def _refine_chunks(
        self,
        chunks: list[CodeChunk],
    ) -> list[CodeChunk]:
        refined_chunks: list[CodeChunk] = []

        for chunk in chunks:
            if len(chunk.content) <= self.chunk_size:
                refined_chunks.append(chunk)
            else:
                sub_chunks = self._split_large_chunk(chunk)
                refined_chunks.extend(sub_chunks)

        return self._add_overlap(refined_chunks)

    def _split_large_chunk(self, chunk: CodeChunk) -> list[CodeChunk]:
        lines = chunk.content.split("\n")
        sub_chunks: list[CodeChunk] = []

        current_chunk = ""
        current_start_line = chunk.start_line
        current_line_count = 0

        for i, line in enumerate(lines):
            line_with_newline = line + "\n" if i < len(lines) - 1 else line

            if (
                len(current_chunk) + len(line_with_newline) > self.chunk_size
                and current_chunk.strip()
            ):
                sub_chunks.append(
                    CodeChunk(
                        content=current_chunk.strip(),
                        start_line=current_start_line,
                        end_line=current_start_line + current_line_count - 1,
                        language=chunk.language,
                        file_path=chunk.file_path,
                    )
                )
                current_chunk = line_with_newline
                current_start_line = chunk.start_line + i
                current_line_count = 1
            else:
                current_chunk += line_with_newline
                current_line_count += 1

        if current_chunk.strip():
            sub_chunks.append(
                CodeChunk(
                    content=current_chunk.strip(),
                    start_line=current_start_line,
                    end_line=current_start_line + current_line_count - 1,
                    language=chunk.language,
                    file_path=chunk.file_path,
                )
            )

        return sub_chunks

    def _add_overlap(self, chunks: list[CodeChunk]) -> list[CodeChunk]:
        if len(chunks) <= 1 or self.chunk_overlap <= 0:
            return chunks

        overlapped_chunks: list[CodeChunk] = []

        for i, chunk in enumerate(chunks):
            content = chunk.content
            metadata = chunk

            if i > 0 and self.chunk_overlap > 0:
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk.content[-self.chunk_overlap :]
                content = overlap_text + "\n" + content
                metadata.start_line = max(
                    1, metadata.start_line - self._get_line_count(overlap_text)
                )

            overlapped_chunks.append(
                CodeChunk(
                    content=content,
                    start_line=metadata.start_line,
                    end_line=metadata.end_line,
                    language=metadata.language,
                    file_path=metadata.file_path,
                )
            )

        return overlapped_chunks

    def _get_line_count(self, text: str) -> int:
        return len(text.split("\n"))

    async def _fallback_text_split(self, code: str, file_path: Path) -> list[CodeChunk]:
        lines = code.split("\n")
        chunks: list[CodeChunk] = []

        current_chunk = ""
        current_start_line = 1

        lang = LANGUAGE_EXTENSIONS.get(file_path.suffix)

        if lang is None:
            return []

        for i, line in enumerate(lines):
            line_with_newline = line + "\n"

            if (
                len(current_chunk) + len(line_with_newline) > self.chunk_size
                and current_chunk.strip()
            ):
                chunks.append(
                    CodeChunk(
                        content=current_chunk.strip(),
                        start_line=current_start_line,
                        end_line=i,
                        language=lang,
                        file_path=str(file_path),
                    )
                )
                current_chunk = line_with_newline
                current_start_line = i + 1
            else:
                current_chunk += line_with_newline

        if current_chunk.strip():
            chunks.append(
                CodeChunk(
                    content=current_chunk.strip(),
                    start_line=current_start_line,
                    end_line=len(lines),
                    language=lang,
                    file_path=str(file_path),
                )
            )

        return chunks
