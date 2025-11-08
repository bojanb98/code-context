# Code Context Core

Core library for semantic code search and indexing. Provides hybrid retrieval, language-aware chunking, and incremental sync (async-first).

## Stack
- Python 3.13+
- Qdrant (vector DB)
- OpenAI-compatible API (e.g., Ollama) for embeddings/explanations
- tree-sitter (chunking), xxhash (hashing), loguru/tenacity (ops)

## Key Interfaces
```python
from core import (
    IndexingService, SearchService,
    EmbeddingService, ExplainerService,
    TreeSitterSplitter, FileSynchronizer,
)
````

`SearchService` expects code and (optionally) doc embedding services; `IndexingService` wires client, synchronizer, splitter, embedding providers, and optional explainer. 

## Correct Usage Example

```python
import asyncio
from pathlib import Path
from qdrant_client import AsyncQdrantClient
from core import (
    IndexingService, SearchService,
    EmbeddingService, ExplainerService,
    TreeSitterSplitter, FileSynchronizer,
)

async def main():
    client = AsyncQdrantClient(url="http://localhost:6333")

    # Embeddings (OpenAI-compatible endpoint, e.g., Ollama)
    code_embed = EmbeddingService(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="vuongnguyen2212/CodeRankEmbed",
        size=768,
    )
    # Optional doc/text embedding service (set to None to disable)
    doc_embed = None

    # Optional code explainer (LLM)
    explainer = ExplainerService(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="gemma3:1b-it-q8_0",
        parallelism=2,
    )

    # Chunking & sync
    splitter = TreeSitterSplitter(chunk_size=2500, chunk_overlap=300, extract_docs=True)
    synchronizer = FileSynchronizer(Path.home() / ".code-context" / "snapshots")

    # Services
    indexing = IndexingService(
        client,
        synchronizer,
        splitter,
        code_embed,
        doc_embed,
        explainer,
    )
    search = SearchService(client, code_embed, doc_embed)  # doc_embed can be None

    # Index
    await indexing.index(Path("./my-project"), force=False)

    results = await search.search(Path("./my-project"), "authentication handler", top_k=5)
    for r in results:
        print(r.relative_path, r.start_line, r.end_line, r.score)

asyncio.run(main())
```

## Graph Edges (experimental)

`core.graph.GraphBuilder` can derive optional GraphRAG edges from the Tree-Sitter chunks that the splitter produces. The builder currently emits four edge types:
- `PARENT_OF`: structural nesting (class → method, function → inner function)
- `CONTINUES`: sequential segments produced when an oversize chunk is split
- `CALLS`: call-site references that resolve to known symbols
- `USES`: identifier/type references pointing to other chunks

Same-file reference edges are disabled by default to keep noise low but can be enabled per invocation.

```python
from core.graph import GraphBuilder

builder = GraphBuilder(include_intra_file_refs=True, include_parents=False)
edges = builder.build(chunks)
for edge in edges:
    print(edge.edge_type, edge.source_id, edge.target_id)
```

Run the builder right after chunking, before embeddings are generated, to keep indexing incremental and avoid re-reading source files.
