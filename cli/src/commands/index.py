from pathlib import Path


async def index_command(
    path: Path = Path("."),
    force: bool = False,
) -> None:
    """Index a codebase for semantic search.

    Args:
        path: Path to the codebase to index (defaults to current directory)
        force: Force complete reindexing instead of incremental updates
    """
    from core import EmbeddingConfig

    from config import load_config
    from service_factory import ServiceFactory

    settings = load_config()
    services = ServiceFactory(settings)

    indexing_service = services.get_indexing_service()
    splitter = services.get_splitter()

    embedding_config = EmbeddingConfig(
        service=services.get_embedding_service(),
        model=settings.embedding.model,
        size=settings.embedding.size,
    )

    await indexing_service.index(path, splitter, embedding_config, force_reindex=force)
