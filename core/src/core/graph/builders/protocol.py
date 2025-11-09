from typing import Protocol, Sequence

from core.splitters import CodeChunk

from .types import GraphEdge


class GraphBuilder(Protocol):

    def build(
        self,
        chunks: Sequence[CodeChunk],
        include_intra_file_refs: bool = True,
    ) -> list[GraphEdge]:
        """Return reference/call edges for the provided chunks."""
        ...
