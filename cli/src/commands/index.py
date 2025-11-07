from pathlib import Path

from core import ExplainerConfig, get_collection_name

from config import save_config


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
    from rich import print

    from config import load_config
    from service_factory import ServiceFactory

    collection_name = get_collection_name(path.expanduser().absolute())

    settings, has_changed = load_config(collection_name)

    if has_changed and not force:
        print(
            "Config has changed since last load. Please rerun command with --force option"
        )
        return

    services = ServiceFactory(settings)

    indexing_service = services.get_indexing_service()
    splitter = services.get_splitter()

    embedding_config = EmbeddingConfig(
        service=services.get_embedding_service(),
        model=settings.embedding.model,
        size=settings.embedding.size,
    )

    explainer_service = services.get_explainer_service()

    explainer_config: ExplainerConfig | None = None

    if explainer_service is not None:
        explainer_config = ExplainerConfig(
            service=explainer_service,
            embedding=EmbeddingConfig(
                service=services.get_embedding_service(),
                model=settings.explainer.embedding.model,
                size=settings.explainer.embedding.size,
            ),
        )

    await indexing_service.index(
        path, splitter, embedding_config, explainer_config, force
    )

    save_config(settings, collection_name)
