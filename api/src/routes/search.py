from core import Context
from fastapi import APIRouter, Query
from loguru import logger

from config import get_context
from models.search import SearchResponse, SearchResult

router = APIRouter()


@router.get("/", response_model=SearchResponse, summary="Semantic code search")
async def search_codebase(
    path: str = Query(..., description="Path to the codebase to search in"),
    query: str = Query(..., description="Search query"),
    limit: int = Query(
        default=15, ge=1, le=100, description="Maximum number of results"
    ),
    context: Context = get_context(),
) -> SearchResponse:
    results = await context.search(path, query, limit)

    if not results:
        logger.info("No results found")
        return SearchResponse(
            results=[],
            query=query,
            path=path,
            limit=limit,
            total_results=0,
        )

    response = SearchResponse(
        results=[
            SearchResult(
                file=r.relative_path,
                start_line=r.start_line,
                end_line=r.end_line,
                score=r.score,
                language=r.language,
                content=r.content,
            )
            for r in results
        ],
        query=query,
        path=path,
        limit=limit,
        total_results=len(results),
    )

    logger.info(f"Found {len(results)} results for query: '{query}'")
    return response
