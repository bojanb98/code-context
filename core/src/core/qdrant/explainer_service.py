import asyncio
import itertools
from dataclasses import dataclass

from openai import AsyncOpenAI as OpenAI
from openai import RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


@dataclass
class ExplainerConfig:
    url: str
    model: str
    api_key: str = ""
    parallelism: int = 1


class ExplainerService:

    _SYSTEM_PROMPT: str = """
    You will receive only source code as input. Return exactly one concise English sentence that captures the code’s purpose and intent - no code, no labels, no examples, no extra sentences.
    """

    _DEFAULT_EXPLANATION: str = "unknown"

    def __init__(self, config: ExplainerConfig) -> None:
        self.openai = OpenAI(base_url=config.url, api_key=config.api_key)
        self.model = config.model
        self.parallelism = config.parallelism
        if config.parallelism < 1:
            raise ValueError("Invalid parallelism")

    @retry(
        wait=wait_exponential(min=5, max=20),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(RateLimitError),
    )
    async def _get_explanation(self, code_chunk: str) -> str:
        response = await self.openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": ExplainerService._SYSTEM_PROMPT},
                {"role": "user", "content": code_chunk},
            ],
        )
        explanation = response.choices[0].message.content
        if explanation is None:
            return ExplainerService._DEFAULT_EXPLANATION
        return explanation

    async def _get_sync_explanations(self, code_chunks: list[str]) -> list[str]:
        explanations: list[str] = []
        for code in code_chunks:
            explanations.append(await self._get_explanation(code))

        return explanations

    async def _get_parallel_explanations(self, code_chunks: list[str]) -> list[str]:
        batches = itertools.batched(code_chunks, self.parallelism)

        explanations: list[str] = []

        for batch in batches:
            tasks = [
                asyncio.create_task(self._get_explanation(chunk)) for chunk in batch
            ]
            results = await asyncio.gather(*tasks)
            explanations.extend(results)

        return explanations

    async def get_explanations(self, code_chunks: list[str]) -> list[str]:
        if self.parallelism == 1:
            return await self._get_sync_explanations(code_chunks)
        return await self._get_parallel_explanations(code_chunks)
