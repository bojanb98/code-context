from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    file: str = Field(..., description="Relative file path")
    start_line: int = Field(..., description="Start line number of the match")
    end_line: int = Field(..., description="End line number of the match")
    score: float = Field(..., description="Similarity score (0-1)")
    language: str = Field(..., description="Programming language")
    content: str = Field(..., description="Matched code content")


class SearchRequest(BaseModel):
    path: str = Field(..., description="Path to the codebase to search in")
    query: str = Field(..., description="Search query")
    limit: int = Field(default=5, ge=1, le=100, description="Maximum number of results")
    extensions: list[str] | None = Field(
        default=None, description="File extensions to filter by"
    )


class SearchResponse(BaseModel):
    results: list[SearchResult] = Field(..., description="Search results")
    query: str = Field(..., description="Original search query")
    path: str = Field(..., description="Path that was searched")
    limit: int = Field(..., description="Maximum results requested")
    total_results: int = Field(..., description="Total number of results found")
