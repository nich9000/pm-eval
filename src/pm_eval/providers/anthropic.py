"""Anthropic Claude provider implementation.

To use:
    from pm_eval.providers import ClaudeProvider
    provider = ClaudeProvider(model="claude-sonnet-4-6")

Requires `anthropic` extra:
    pip install pm-eval[anthropic]

Reads ANTHROPIC_API_KEY from the environment by default.
"""

import time

from pm_eval.providers.base import GraderProvider, ProviderResponse


# Per-1M-token pricing in USD. Update as pricing changes.
ANTHROPIC_PRICING = {
    "claude-opus-4-6":            {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6":          {"input":  3.0, "output": 15.0},
    "claude-haiku-4-5-20251001":  {"input":  1.0, "output":  5.0},
}


class ClaudeProvider(GraderProvider):
    """Judge using Anthropic's Claude models."""

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None):
        # Lazy import so the module loads without `anthropic` installed if user picks a different provider.
        from anthropic import Anthropic
        self._model = model
        self._client = Anthropic(api_key=api_key)  # falls back to ANTHROPIC_API_KEY env

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    def judge(self, prompt: str, *, max_tokens: int = 2048,
              temperature: float = 0.0) -> ProviderResponse:
        start = time.time()
        message = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = int((time.time() - start) * 1000)

        # Stitch together all text blocks from the response.
        text = "".join(getattr(b, "text", "") for b in message.content)

        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        pricing = ANTHROPIC_PRICING.get(
            self._model,
            {"input": 3.0, "output": 15.0},  # default to Sonnet pricing if unknown
        )
        cost = (input_tokens / 1_000_000) * pricing["input"] + (output_tokens / 1_000_000) * pricing["output"]

        return ProviderResponse(
            text=text,
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
        )
