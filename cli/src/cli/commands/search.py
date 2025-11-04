from pathlib import Path
from typing import Literal

from core import SearchResult

OutputType = Literal["simple", "json", "simple-json"]


def json_format(results: list[SearchResult]) -> str:
    import json
    from dataclasses import asdict

    formatted_results = []

    for result in results:
        formatted_result = asdict(result)
        formatted_results.append(formatted_result)

    return json.dumps(
        {"results": formatted_results, "total": len(formatted_results)}, indent=2
    )


def json_format_simple(results: list[SearchResult]) -> str:
    import json

    formatted_results = []

    for result in results:
        formatted_result = {"content": result.content.strip()}
        formatted_results.append(formatted_result)

    return json.dumps(formatted_results)


def print_results(results: list[SearchResult], output_type: OutputType) -> None:
    from rich import print, print_json
    from rich.syntax import Syntax

    if output_type == "json":
        print_json(json_format(results))
    if output_type == "simple-json":
        print_json(json_format_simple(results))
    else:
        for result in results:
            print(f"Path: {result.relative_path}")
            print(f"Start line: {result.start_line}")
            print(f"End line: {result.end_line}")
            if result.explanation:
                print(f"Explanation: {result.explanation}")
            print(Syntax(result.content.strip(), result.language, line_numbers=False))


async def search_command(
    query: str,
    path: Path = Path("."),
    limit: int = 5,
    output: OutputType = "simple",
) -> None:
    """Search indexed code semantically.

    Args:
        query: Search query text
        path: Path to search in (defaults to current directory)
        limit: Maximum number of results to return (1-50)
        output: Output format: simple (default), json (full details), simple-json (content only)
    """
    from cli.config import load_config
    from cli.service_factory import ServiceFactory

    settings = load_config()
    services = ServiceFactory(settings)

    search_service = services.get_search_service()

    results = await search_service.search(path, query, top_k=limit)

    print_results(results, output)
