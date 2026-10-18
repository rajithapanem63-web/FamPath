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
    """Intelligent mock provider that answers from context when no LLM API key is set."""

    model = "fampath-mock-v1"

    # Common Q&A about Indian engineering college admissions
    KNOWLEDGE_BASE = {
        "eapcet": "AP EAPCET (Engineering, Agriculture and Pharmacy Common Entrance Test) is the main entrance exam for engineering colleges in Andhra Pradesh. TS EAPCET is the equivalent exam for Telangana state. Ranks are used for seat allotment through web counselling.",
        "jee": "JEE Mains is conducted by NTA for admission to NITs, IIITs, CFTIs and other engineering colleges. JEE Advanced is for IIT admissions. JEE Main ranks are used for AP/TS EAPCET as well in some colleges.",
        "category": "Categories for reservations include OC (Open Category/General), BC-A, BC-B, BC-C, BC-D, BC-E (Backward Classes), SC (Scheduled Caste), ST (Scheduled Tribe), and EWS (Economically Weaker Section). Each category has different cut-off ranks.",
        "counselling": "Web counselling is conducted phase-wise. Students must register, pay fee, enter options (colleges & branches), and attend certificate verification. Seat allotment happens based on rank, category, and available seats.",
        "cse": "Computer Science Engineering (CSE) is the most popular branch. It covers programming, algorithms, data structures, AI, and software development. CSE graduates work in software companies, startups, and research.",
        "ece": "Electronics & Communication Engineering (ECE) covers circuits, signals, embedded systems, VLSI, and communications. ECE graduates work in telecom, semiconductor, and electronics industries.",
        "mech": "Mechanical Engineering covers thermodynamics, manufacturing, machine design, and fluid mechanics. It offers careers in automotive, aerospace, and manufacturing sectors.",
        "rank": "A lower rank number means a better rank. For example, rank 1000 is better than rank 50000. Closing rank is the highest (worst) rank that got a seat in previous years.",
        "college": "Popular engineering colleges in Telangana include JNTUH, CBIT, MVSR, VNR VJIET, Vasavi, and BITS Hyderabad. In Andhra Pradesh, JNTUA, SVEC, SRKR, and GITAM are well-known.",
        "fee": "Government colleges typically charge Rs. 30,000–60,000 per year. Private unaided colleges charge Rs. 80,000–1,80,000 per year. Deemed universities may charge Rs. 1,50,000–3,00,000 per year.",
        "cutoff": "Cutoff ranks vary by college, branch, category, and year. Top CSE branches at premier colleges may close around rank 5,000–20,000 in OC category for TS EAPCET.",
        "placement": "Placement rates vary by college and branch. CSE and IT branches generally have 80–95% placement at good colleges. Average packages range from Rs. 3–8 LPA at most colleges, with top companies offering Rs. 10–25 LPA.",
        "default": "I can help you with questions about engineering college admissions in AP and Telangana. You can ask me about entrance exams (EAPCET, JEE), categories, counselling process, branches (CSE, ECE, MECH), college fees, placements, and cutoff ranks.",
    }

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1500,
        **kwargs: Any,
    ) -> LLMResponse:
        # Extract the question from user_message
        question = user_message.lower()
        if "Question:" in user_message:
            question = user_message.split("Question:")[-1].strip().lower()

        # Find relevant answer from knowledge base
        answer = None
        for keyword, text in self.KNOWLEDGE_BASE.items():
            if keyword in question:
                answer = text
                break

        if answer is None:
            # Check context for any relevant info
            if "Context:" in user_message and len(user_message.split("Context:")[-1].strip()) > 50:
                ctx = user_message.split("Context:")[-1].split("Question:")[0].strip()
                if len(ctx) > 100:
                    answer = f"Based on the available information: {ctx[:400]}..."
                else:
                    answer = self.KNOWLEDGE_BASE["default"]
            else:
                answer = self.KNOWLEDGE_BASE["default"]

        response = {
            "answer": answer,
            "citations": [{"source": "FamPath Knowledge Base", "year": 2024}],
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
