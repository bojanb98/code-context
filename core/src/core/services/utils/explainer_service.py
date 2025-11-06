import asyncio
import itertools

from loguru import logger
from openai import AsyncOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class ExplainerService:

    _SYSTEM_PROMPT: str = """
    You will receive only source code as input. Return exactly one concise English sentence that captures the code’s purpose and intent - no code, no labels, no examples, no extra sentences.
    """

    _DEFAULT_EXPLANATION: str = "unknown"

    def __init__(self, base_url: str, api_key: str, parallelism: int = 1) -> None:
        self.openai = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.parallelism = parallelism

    @retry(
        wait=wait_exponential(min=5, max=20),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(RateLimitError),
        before_sleep=lambda x: logger.warning("Rate limit hit {} {}", x.fn, x.args),
    )
    async def _get_explanation(self, code_chunk: str, model: str) -> str:
        response = await self.openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ExplainerService._SYSTEM_PROMPT},
                {"role": "user", "content": code_chunk},
            ],
        )
        explanation = response.choices[0].message.content
        if explanation is None:
            return ExplainerService._DEFAULT_EXPLANATION
        return explanation

    async def _get_sync_explanations(
        self, code_chunks: list[str], model: str
    ) -> list[str]:
        explanations: list[str] = []
        for code in code_chunks:
            explanations.append(await self._get_explanation(code, model))

        return explanations

    async def _get_parallel_explanations(
        self, code_chunks: list[str], model: str
    ) -> list[str]:
        batches = itertools.batched(code_chunks, self.parallelism)

        explanations: list[str] = []

        for batch in batches:
            tasks = [
                asyncio.create_task(self._get_explanation(chunk, model))
                for chunk in batch
            ]
            results = await asyncio.gather(*tasks)
            explanations.extend(results)

        return explanations

    async def get_explanations(self, code_chunks: list[str], model: str) -> list[str]:
        if self.parallelism == 1:
            return await self._get_sync_explanations(code_chunks, model)
        return await self._get_parallel_explanations(code_chunks, model)
