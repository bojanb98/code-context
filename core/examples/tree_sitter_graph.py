import asyncio
from pathlib import Path
from timeit import default_timer as timer

from pyvis.network import Network

from core.graph import GraphBuilder, GraphEdge
from core.graph.types import GraphEdgeType
from core.splitters import CodeChunk, TreeSitterSplitter
from core.sync.scanner import scan_and_hash_all
from core.sync.util import DEFAULT_IGNORE_PATTERNS


async def discover_files(root: Path) -> list[Path]:
    records = await scan_and_hash_all(root, DEFAULT_IGNORE_PATTERNS)
    return [root / rel for rel in sorted(records.keys())]


async def chunk_files(root: Path, splitter: TreeSitterSplitter) -> list[CodeChunk]:
    chunks: list[CodeChunk] = []
    for file_path in await discover_files(root):
        try:
            source = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relative_path = file_path.relative_to(root)
        chunks.extend(await splitter.split(source, relative_path))
    return chunks


async def get_data(
    path: Path, include_same_file_refs: bool, include_parents: bool
) -> tuple[list[CodeChunk], list[GraphEdge]]:
    splitter = TreeSitterSplitter(chunk_size=2000, chunk_overlap=200)
    start = timer()
    chunks = await chunk_files(path, splitter)
    end = timer()
    print(len(chunks), end - start)

    builder = GraphBuilder(
        include_intra_file_refs=include_same_file_refs, include_parents=include_parents
    )
    start = timer()
    edges = builder.build(chunks)
    end = timer()
    print(len(edges), end - start)
    print(len([e for e in edges if e.edge_type == GraphEdgeType.CALLS]))

    return chunks, edges


async def build_graph(chunks: list[CodeChunk], edges: list[GraphEdge]) -> None:
    net = Network(height="750px", width="100%", directed=True)

    for c in chunks:
        first_line = c.content.splitlines()[0].strip()
        label = str(c.file_path) + "\n" + first_line
        net.add_node(c.id, label)

    for edge in edges:
        net.add_edge(edge.source_id, edge.target_id, title=edge.edge_type)

    net.show("test.html", notebook=False)


async def main() -> None:
    target = Path("./").expanduser().resolve()
    same_file_refs = True
    include_parents = False
    chunks, edges = await get_data(target, same_file_refs, include_parents)
    await build_graph(chunks, edges)


if __name__ == "__main__":
    asyncio.run(main())
