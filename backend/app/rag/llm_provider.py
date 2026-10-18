"""
LLM provider abstraction. Implements a provider-agnostic interface
so the underlying model can be swapped without touching business logic.
"""
from __future__ import annotations

import json
from typing import Any, Protocol, runtime_checkable

import structlog

logger = structlog.get_logger(__name__)


class LLMResponse:
    def __init__(self, content: str, model: str) -> None:
        self.content = content
        self.model = model


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1500,
        **kwargs: Any,
    ) -> LLMResponse: ...


class MockProvider:
    """Returns deterministic mock responses for testing."""

    model = "mock-model"

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1500,
        **kwargs: Any,
    ) -> LLMResponse:
        response = {
            "answer": "This is a mock answer based on the provided context.",
            "citations": [{"source": "Mock Knowledge Base", "year": 2024}],
            "refused": False,
        }
        return LLMResponse(content=json.dumps(response), model=self.model)


class AnthropicProvider:
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 30) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import anthropic  # type: ignore[import-untyped]
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1500,
        **kwargs: Any,
    ) -> LLMResponse:
        import httpx

        client = self._get_client()
        for attempt in range(3):
            try:
                response = await client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )
                return LLMResponse(
                    content=response.content[0].text,
                    model=self._model,
                )
            except (httpx.TimeoutException, Exception) as exc:
                if attempt == 2:
                    logger.error("llm_api_failed", error=str(exc))
                    raise
                import asyncio
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError("LLM API unreachable")


def get_llm_provider(settings: Any) -> LLMProvider:
    """Factory: return the configured LLM provider."""
    if settings.LLM_PROVIDER == "anthropic":
        return AnthropicProvider(
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
        )
    return MockProvider()
