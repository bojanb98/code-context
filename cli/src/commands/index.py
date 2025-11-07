from pathlib import Path

from core import get_collection_name

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

    await indexing_service.index(path, force)

    save_config(settings, collection_name)
