import itertools

from openai import AsyncOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

Embedding = list[float]


class EmbeddingService:

    def __init__(self, base_url: str, api_key: str) -> None:
        self.openai = AsyncOpenAI(base_url=base_url, api_key=api_key)

    @retry(
        wait=wait_exponential(min=5, max=20),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(RateLimitError),
    )
    async def generate_embedding(self, query: str, model: str) -> Embedding:
        response = await self.openai.embeddings.create(input=query, model=model)

        return response.data[0].embedding

    async def generate_embeddings(
        self, queries: list[str], model: str, batch_size: int = 32
    ) -> list[Embedding]:
        all_embeddings: list[Embedding] = []

        for query_batch in itertools.batched(queries, batch_size):
            response = await self.openai.embeddings.create(
                input=query_batch, model=model
            )
            embedding_batch = [d.embedding for d in response.data]
            all_embeddings.extend(embedding_batch)

        return all_embeddings
