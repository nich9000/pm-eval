"""Anthropic Claude provider implementation.

To use:
    from pm_eval.providers import ClaudeProvider
    provider = ClaudeProvider(model="claude-sonnet-4-6")

Requires `anthropic` extra:
    pip install pm-eval[anthropic]
"""

from pm_eval.providers.base import GraderProvider, ProviderResponse


class ClaudeProvider(GraderProvider):
    """Judge using Anthropic's Claude models.

    TODO (v0.1):
      - Initialize anthropic.Anthropic client from env (ANTHROPIC_API_KEY).
      - Wire judge() to client.messages.create with max_tokens, temperature.
      - Capture usage tokens for cost tracking.
      - Compute cost_usd from model + token counts.
      - Capture latency_ms.
    """

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None):
        self._model = model
        self._api_key = api_key  # if None, will read from ANTHROPIC_API_KEY env
        # TODO: lazy import anthropic and instantiate client

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    def judge(self, prompt: str, *, max_tokens: int = 2048,
              temperature: float = 0.0) -> ProviderResponse:
        raise NotImplementedError("ClaudeProvider.judge — implement in v0.1")
