import asyncio
from pathlib import Path
from timeit import default_timer as timer

from fastembed.common.model_description import DenseModelDescription, ModelSource
from fastembed.text.onnx_embedding import supported_onnx_models
from loguru import logger

from core import Context
from core.indexing_service import IndexingConfig
from core.qdrant import QdrantConfig
from core.sync import SynchronizerConfig

logger.level("DEBUG")


async def run_test():
    model = "sirasagi62/code-rank-embed-onnx"
    supported_onnx_models.append(
        DenseModelDescription(
            model=model,
            description="Custom CodeRankEmbed model",
            license="",
            size_in_GB=0.6,
            sources=ModelSource(hf=model),
            dim=768,
            model_file="model.onnx",
        )
    )

    context = Context(
        QdrantConfig(model),
        IndexingConfig(64, 2500, 300, SynchronizerConfig("./snapshots")),
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
