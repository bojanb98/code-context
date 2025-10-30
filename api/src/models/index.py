from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    path: str = Field(..., description="Path to the codebase to index")
    force: bool = Field(
        default=False, description="Force reindexing even if already indexed"
    )


class ClearIndexRequest(BaseModel):
    path: str = Field(..., description="Path to the codebase to clear index for")
