"""The only module that talks to OpenRouter."""

import os
import time
from typing import Optional, Protocol, TypeVar

from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel

from .config import ModelConfig

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

T = TypeVar("T", bound=BaseModel)


class QueryModelError(Exception):
    pass


class ChatClient(Protocol):
    """Interface used by approaches and the judge, so tests can pass a fake client."""

    def chat(self, messages: list[dict], cfg: ModelConfig) -> str: ...

    def parse(self, messages: list[dict], cfg: ModelConfig, response_format: type[T]) -> Optional[T]: ...


class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None, retries: int = 3, backoff: float = 2.0):
        from openai import OpenAI

        load_dotenv(find_dotenv(usecwd=True))
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise QueryModelError("OPENROUTER_API_KEY is not set (environment or .env)")
        self.client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
        self.retries = retries
        self.backoff = backoff

    def _with_retries(self, fn):
        last = None
        for attempt in range(self.retries):
            try:
                return fn()
            except QueryModelError as e:
                last = e
            except Exception as e:  # network / rate limit / provider errors
                last = QueryModelError(f"API call failed: {e}")
            time.sleep(self.backoff * (attempt + 1))
        raise last

    def chat(self, messages: list[dict], cfg: ModelConfig) -> str:
        # Strip our bookkeeping keys (e.g. "turn") before sending.
        msgs = [{"role": m["role"], "content": m["content"]} for m in messages]

        def call():
            response = self.client.chat.completions.create(
                model=cfg.model,
                messages=msgs,
                max_tokens=cfg.max_tokens,
                temperature=cfg.temperature,
            )
            if not getattr(response, "choices", None):
                raise QueryModelError(f"No choices in response: {response!r}")
            msg = response.choices[0].message
            if msg is None or not msg.content:
                raise QueryModelError(f"Empty message content in response: {response!r}")
            return msg.content

        return self._with_retries(call)

    def parse(self, messages: list[dict], cfg: ModelConfig, response_format: type[T]) -> Optional[T]:
        def call():
            resp = self.client.chat.completions.parse(
                model=cfg.model,
                messages=messages,
                temperature=cfg.temperature,
                max_completion_tokens=cfg.max_tokens,
                response_format=response_format,
            )
            return resp.choices[0].message.parsed

        try:
            return self._with_retries(call)
        except QueryModelError as e:
            print(f"API Error: {e}")
            return None
