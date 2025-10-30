from fastapi import APIRouter

from config import ContextDep
from models.index import ClearIndexRequest, IndexRequest

router = APIRouter()


@router.post("/", summary="Index a codebase")
async def index_codebase(request: IndexRequest, context: ContextDep):
    await context.index(request.path, request.force)


@router.delete("/", summary="Clear index")
async def clear_index(request: ClearIndexRequest, context: ContextDep):
    await context.clear_index(request.path)
