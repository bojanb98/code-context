from pathlib import Path

from core import SearchResult


async def mcp_command() -> None:
    """
    Start MCP server exposing search functionality.
    """
    from mcp.server.fastmcp import FastMCP
    from pydantic import PositiveInt

    from config import load_config
    from service_factory import ServiceFactory

    settings = load_config()
    services = ServiceFactory(settings)

    search_service = services.get_search_service()

    mcp = FastMCP("code-context-search")

    @mcp.tool()
    async def search_code(
        query: str, path: str = ".", limit: PositiveInt = 5
    ) -> list[SearchResult]:
        """
        Search indexed code semantically. Provide concise and direct query capturing the intent.

        Args:
            query: Search query text (required).
            path: Path to search in (defaults to current directory)
            limit: Maximum number of results to return (1-50)

        Returns:
            List of search results containing file paths, line numbers,
            similarity scores, code content, and explanations when available.
        """

        results = await search_service.search(Path(path), query, top_k=limit)

        return results

    mcp.run(transport="stdio")
