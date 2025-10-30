import asyncio
from pathlib import Path
from timeit import default_timer as timer

from loguru import logger

from core import Context
from core.indexing_service import IndexingConfig
from core.qdrant import QdrantConfig
from core.qdrant.client import EmbeddingConfig
from core.sync import SynchronizerConfig

logger.level("DEBUG")


async def run_test():
    model = "vuongnguyen2212/CodeRankEmbed"

    context = Context(
        QdrantConfig(
            EmbeddingConfig(
                model,
                provider="openai",
                url="http://localhost:11434/v1",
                size=768,
            ),
            "server",
            "localhost:6333",
        ),
        IndexingConfig(
            64,
            2500,
            300,
            SynchronizerConfig("./snapshots"),
        ),
    )

    path = Path("./").resolve().absolute()

    start = timer()

    await context.index(path)

    end = timer()

    print(end - start)

    start = timer()

    results = await context.search(path, "Code indexing")

    end = timer()

    print(end - start)

    for r in results:
        __import__("pprint").pprint(r)


if __name__ == "__main__":
    asyncio.run(run_test())
