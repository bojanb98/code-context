from collections import defaultdict
from typing import Sequence

from tree_sitter_language_pack import SupportedLanguage

from core.splitters import CodeChunk

from .builders import GraphEdge, GraphEdgeType
from .factory import get_builder


class GraphEdgeBuilder:
    def __init__(
        self, include_intra_file_refs: bool = False, include_parents: bool = True
    ) -> None:
        self.include_intra_file_refs = include_intra_file_refs
        self.include_parents = include_parents

    def build(self, chunks: Sequence[CodeChunk]) -> list[GraphEdge]:
        edges: list[GraphEdge] = []
        if self.include_parents:
            edges.extend(self._parent_edges(chunks))
        edges.extend(self._continuation_edges(chunks))
        edges.extend(self._language_edges(chunks))
        return edges

    def _parent_edges(self, chunks: Sequence[CodeChunk]) -> list[GraphEdge]:
        lookup = {ref.id: ref for ref in chunks}
        edges: list[GraphEdge] = []

        for ref in chunks:
            parent_id = ref.parent_chunk_id
            if not parent_id:
                continue
            if parent_id not in lookup:
                continue
            edges.append(
                GraphEdge(
                    source_id=parent_id,
                    target_id=ref.id,
                    edge_type=GraphEdgeType.PARENT_OF,
                )
            )

        return edges

    def _continuation_edges(self, chunks: Sequence[CodeChunk]) -> list[GraphEdge]:
        grouped: dict[int, list[CodeChunk]] = defaultdict(list)

        for ref in chunks:
            if ref.node is None:
                continue
            grouped[id(ref.node)].append(ref)

        edges: list[GraphEdge] = []
        for refs in grouped.values():
            if len(refs) < 2:
                continue
            ordered = sorted(
                refs,
                key=lambda r: (r.start_line, r.end_line),
            )
            for left, right in zip(ordered, ordered[1:]):
                edges.append(
                    GraphEdge(
                        source_id=left.id,
                        target_id=right.id,
                        edge_type=GraphEdgeType.CONTINUES,
                    )
                )

        return edges

    def _language_edges(self, chunks: Sequence[CodeChunk]) -> list[GraphEdge]:
        grouped: dict[SupportedLanguage, list[CodeChunk]] = defaultdict(list)
        for ref in chunks:
            grouped[ref.language].append(ref)

        edges: list[GraphEdge] = []
        for language, refs in grouped.items():
            builder = get_builder(language)
            edges.extend(builder.build(refs, self.include_intra_file_refs))
        return edges
