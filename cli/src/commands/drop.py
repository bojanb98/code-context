from pathlib import Path

from core import get_collection_name


async def drop_command(
    path: Path = Path("."),
) -> None:
    """Remove a codebase from the index.

    Args:
        path: Path to the codebase to remove from index (defaults to current directory)
    """
    from config import load_config
    from service_factory import ServiceFactory

    collection_name = get_collection_name(path.expanduser().absolute())

    settings, _ = load_config()
    services = ServiceFactory(settings)

    indexing_service = services.get_indexing_service()

    await indexing_service.delete(path)
