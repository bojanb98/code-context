from pathlib import Path

from loguru import logger
from tree_sitter import Node, Parser
from tree_sitter_language_pack import SupportedLanguage, get_parser

from .base import BaseSplitter
from .types import CodeChunk
from .utils import _LANGUAGE_EXTENSIONS, SPLITTABLE_NODE_TYPES

# Body-node candidates across supported grammars.
_BODY_NODE_TYPES = {
    "block",  # java / csharp / rust / go / many C-like bodies
    "suite",  # python
    "statement_block",  # js / ts
    "compound_statement",  # c / cpp
}

# String literal node names commonly used across grammars.
_STRING_NODE_TYPES = {
    "string",  # js / py (container)
    "string_literal",  # java / c / cpp / csharp / rust / scala / kotlin / swift
    "interpreted_string_literal",  # go
    "raw_string_literal",  # go
    "string_fragment",  # appears within string nodes in some grammars
}

# Comment node names across grammars.
_COMMENT_NODE_TYPES = {"comment", "line_comment", "block_comment"}

# Languages where an inline string as the first statement *inside* the body is a docstring.
_INLINE_DOCSTRING_LANGS = {"python"}

# Doc-comment prefixes that usually indicate documentation-style comments.
_DOC_COMMENT_PREFIXES = (
    "/**",  # Javadoc / JSDoc / KDoc / Swift block docs
    "/*!",  # Doxygen / special doc block
    "///",  # C# / C++ / Rust / Swift line docs
    "//!",
    "##",  # sometimes used as doc in scripts
)


class TreeSitterSplitter(BaseSplitter):

    def __init__(
        self,
        chunk_size: int = 2500,
        chunk_overlap: int = 300,
        extract_docs: bool = False,
    ) -> None:
        super().__init__(chunk_size, chunk_overlap)
        self._parsers: dict[SupportedLanguage, Parser] = {}
        self.extract_docs = extract_docs

    # ----------------------- Public API -----------------------

    async def split(self, code: str, file_path: Path) -> list[CodeChunk]:
        """
        Split file content into CodeChunk units using Tree-Sitter.

        Args:
            code: File content
            file_path: Path to the file

        Returns:
            list[CodeChunk]
        """
        lang = _LANGUAGE_EXTENSIONS.get(file_path.suffix.lower().strip())
        if lang is None:
            logger.debug(f"File type not supported by Tree-Sitter: {file_path.suffix}")
            return await self._fallback_text_split(code, file_path)

        parser = self._get_parser(lang)
        if not parser:
            return await self._fallback_text_split(code, file_path)

        try:
            tree = parser.parse(code.encode("utf-8"))
            if not tree or not tree.root_node:
                logger.warning(f"Failed to parse AST for {file_path.name}")
                return await self._fallback_text_split(code, file_path)

            chunks = self._extract_chunks(tree.root_node, lang, code, file_path)
            refined_chunks = await self._refine_chunks(chunks)
            return refined_chunks

        except Exception as e:
            logger.warning(f"Tree-Sitter failed for {file_path.name}: {e}")
            return await self._fallback_text_split(code, file_path)

    # ----------------------- Core traversal -----------------------

    def _extract_chunks(
        self,
        node: Node,
        lang: SupportedLanguage,
        code: str,
        file_path: Path,
    ) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []
        splittable_types = SPLITTABLE_NODE_TYPES.get(lang)

        if not splittable_types:
            raise RuntimeError(f"Invalid splittable types for {lang}")

        def traverse(current_node: Node) -> None:
            if current_node.type in splittable_types:
                start_line = current_node.start_point[0] + 1
                end_line = current_node.end_point[0] + 1

                content, doc = self._node_code_and_doc(current_node, lang, code)

                if content and content.strip():
                    chunks.append(
                        CodeChunk(
                            content=content.strip(),
                            start_line=start_line,
                            end_line=end_line,
                            language=lang,
                            file_path=str(file_path),
                            doc=doc.strip() if doc is not None else None,
                        )
                    )

            for child in current_node.children:
                traverse(child)

        traverse(node)

        if not chunks:
            total_lines = len(code.splitlines()) or 1
            chunks.append(
                CodeChunk(
                    content=code.strip(),
                    start_line=1,
                    end_line=total_lines,
                    language=lang,
                    file_path=str(file_path),
                    doc=None,
                )
            )

        return chunks

    # ----------------------- Parser helpers -----------------------

    def _get_parser(self, lang: SupportedLanguage) -> Parser | None:
        if lang in self._parsers:
            return self._parsers[lang]
        try:
            parser = get_parser(lang)
            self._parsers[lang] = parser
            logger.debug(f"Loaded tree-sitter parser for {lang}")
            return parser
        except Exception as e:
            logger.warning(f"Failed to load tree-sitter parser for {lang}: {e}")
            return None

    # ----------------------- Byte slicing -----------------------

    def _slice(self, code: str, start: int, end: int) -> str:
        return code.encode("utf-8")[start:end].decode("utf-8")

    # ----------------------- Doc extraction core -----------------------

    def _node_code_and_doc(
        self, node: Node, lang: SupportedLanguage, code: str
    ) -> tuple[str, str | None]:
        node_text = self._slice(code, node.start_byte, node.end_byte)
        if not self.extract_docs:
            return node_text, None

        inline_doc: str | None = None
        code_wo_inline: str = node_text

        # 1) Inline docstring inside the node (Python).
        if lang in _INLINE_DOCSTRING_LANGS:
            inline_doc, code_wo_inline = self._extract_inline_docstring(node, code)

        # 2) Leading documentation comments outside the node (all languages).
        leading_doc = self._gather_leading_doc_comment_block(node, code)

        # Prefer inline doc if present; otherwise take leading doc if present.
        if inline_doc:
            return code_wo_inline, self._normalize_doc_text(inline_doc)
        if leading_doc:
            return node_text, self._normalize_doc_text(leading_doc)

        return node_text, None

    def _extract_inline_docstring(
        self, node: Node, code: str
    ) -> tuple[str | None, str]:
        full = self._slice(code, node.start_byte, node.end_byte)
        body = self._find_body_child(node)
        if not body or not body.named_children:
            return None, full

        first_stmt = body.named_children[0]
        # Pattern: expression_statement -> (string|string_literal|...)
        if first_stmt.type == "expression_statement" and first_stmt.named_children:
            str_node = first_stmt.named_children[0]
            if str_node.type in _STRING_NODE_TYPES:
                raw_doc = self._slice(code, str_node.start_byte, str_node.end_byte)
                doc_text = self._unquote_string_literal(raw_doc)

                before = self._slice(code, node.start_byte, first_stmt.start_byte)
                after = self._slice(code, first_stmt.end_byte, node.end_byte)
                new_full = (before + after).strip()
                return doc_text, (new_full if new_full else full)

        return None, full

    def _unquote_string_literal(self, s: str) -> str:
        if not s:
            return s

        # Strip leading/trailing whitespace once (docstrings rarely need exact indentation here)
        s = s.strip()

        # Remove prefixes (any combination and order of r/u/f/b, case-insensitive)
        i = 0
        while i < len(s) and s[i].lower() in {"r", "u", "f", "b"}:
            i += 1
        prefix = s[:i]
        body = s[i:]

        # Triple quotes
        for q in ('"""', "'''"):
            if body.startswith(q) and body.endswith(q) and len(body) >= 2 * len(q):
                return body[len(q) : -len(q)]

        # Single/double quotes
        for q in ('"', "'"):
            if body.startswith(q) and body.endswith(q) and len(body) >= 2:
                return body[1:-1]

        # If prefixes ended up consuming entire string or malformed quotes, just return original
        return s[len(prefix) :] if prefix and len(prefix) < len(s) else s

    def _gather_leading_doc_comment_block(self, node: Node, code: str) -> str | None:
        prev = node.prev_sibling
        if prev is None:
            return None

        comments: list[str] = []

        while prev and prev.type in _COMMENT_NODE_TYPES:
            comments.append(self._slice(code, prev.start_byte, prev.end_byte))
            prev = prev.prev_sibling

        if not comments:
            return None

        comments.reverse()
        block = "\n".join(comments).strip()
        if not block:
            return None

        lines = [ln.lstrip() for ln in block.splitlines()]
        has_doc_prefix = any(ln.startswith(_DOC_COMMENT_PREFIXES) for ln in lines)

        if not has_doc_prefix:
            consecutive = sum(
                1 for ln in lines if ln.startswith("//") or ln.startswith("#")
            )
            if consecutive < 2:
                return None

        return block

    def _find_body_child(self, node: Node) -> Node | None:
        for ch in node.named_children:
            if ch.type in _BODY_NODE_TYPES:
                return ch
        return None

    # ----------------------- Doc normalization -----------------------

    def _normalize_doc_text(self, text: str) -> str:
        lines = text.splitlines()
        out: list[str] = []
        in_block = False

        for raw in lines:
            s = raw.strip()

            # Start of block comment
            if s.startswith("/**") or s.startswith("/*!") or s.startswith("/*"):
                in_block = True
                # Drop the opener itself; keep any content after it.
                s = s[3:].lstrip("!*").strip()
                if not s:
                    continue

            # End of block comment
            if in_block and s.endswith("*/"):
                s = s[:-2].rstrip()
                in_block = False
                if not s:
                    continue

            # Strip common line prefixes
            if s.startswith("///") or s.startswith("//!") or s.startswith("//"):
                if s.startswith("///"):
                    s = s[3:].lstrip()
                elif s.startswith("//!"):
                    s = s[3:].lstrip()
                else:
                    s = s[2:].lstrip()
            elif s.startswith("*"):
                s = s[1:].lstrip()
            elif s.startswith("##"):
                s = s[2:].lstrip()
            elif s.startswith("#"):
                s = s[1:].lstrip()

            out.append(s)

        cleaned = "\n".join(out).strip()
        return cleaned or text

    # ----------------------- Refinement & fallback -----------------------

    async def _refine_chunks(self, chunks: list[CodeChunk]) -> list[CodeChunk]:
        refined: list[CodeChunk] = []

        for chunk in chunks:
            if len(chunk.content) <= self.chunk_size:
                refined.append(chunk)
            else:
                subs = self._split_large_chunk(chunk)
                subs = self._add_overlap(subs)
                refined.extend(subs)

        return refined

    def _split_large_chunk(self, chunk: CodeChunk) -> list[CodeChunk]:
        lines = chunk.content.split("\n")
        sub_chunks: list[CodeChunk] = []

        current_chunk = ""
        current_start_line = chunk.start_line
        current_line_count = 0

        for i, line in enumerate(lines):
            line_with_newline = line + ("\n" if i < len(lines) - 1 else "")

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
                        doc=chunk.doc,
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
                    doc=chunk.doc,
                )
            )

        return sub_chunks

    def _add_overlap(self, chunks: list[CodeChunk]) -> list[CodeChunk]:
        if len(chunks) <= 1 or self.chunk_overlap <= 0:
            return chunks

        overlapped: list[CodeChunk] = []

        for i, chunk in enumerate(chunks):
            content = chunk.content
            start_line = chunk.start_line
            end_line = chunk.end_line

            if i > 0:
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk.content[-self.chunk_overlap :]
                content = (overlap_text + "\n" + content) if overlap_text else content
                # Adjust start_line based on overlap's line count
                start_line = max(1, start_line - self._get_line_count(overlap_text))

            overlapped.append(
                CodeChunk(
                    content=content,
                    start_line=start_line,
                    end_line=end_line,
                    language=chunk.language,
                    file_path=chunk.file_path,
                    doc=chunk.doc,
                )
            )

        return overlapped

    def _get_line_count(self, text: str) -> int:
        return len(text.splitlines()) if text else 0

    async def _fallback_text_split(self, code: str, file_path: Path) -> list[CodeChunk]:
        lang = _LANGUAGE_EXTENSIONS.get(file_path.suffix.lower().strip())
        if lang is None:
            return []

        lines = code.split("\n")
        chunks: list[CodeChunk] = []

        current_chunk = ""
        current_start_line = 1

        for i, line in enumerate(lines):
            line_with_newline = line + ("\n" if i < len(lines) - 1 else "")

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
                        doc=None,
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
                    doc=None,
                )
            )

        return chunks
