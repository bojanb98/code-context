from dataclasses import dataclass
from enum import Enum

from core.splitters import CodeChunk


class GraphEdgeType(str, Enum):
    PARENT_OF = "PARENT_OF"
    CONTINUES = "CONTINUES"
    CALLS = "CALLS"
    USES = "USES"


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    edge_type: GraphEdgeType


@dataclass(frozen=True)
class ChunkRef:
    chunk_id: str
    chunk: CodeChunk
