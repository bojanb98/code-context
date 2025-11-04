from pathlib import Path


async def drop_command(
    path: Path = Path("."),
) -> None:
    """Remove a codebase from the index.

    Args:
        path: Path to the codebase to remove from index (defaults to current directory)
    """
    from cli.config import load_config
    from cli.service_factory import ServiceFactory

    settings = load_config()
    services = ServiceFactory(settings)

    indexing_service = services.get_indexing_service()

    await indexing_service.delete(path)
