"""OpenAI GPT provider implementation.

To use:
    from pm_eval.providers import OpenAIProvider
    provider = OpenAIProvider(model="gpt-4o")

Requires `openai` extra:
    pip install pm-eval[openai]
"""

from pm_eval.providers.base import GraderProvider, ProviderResponse


class OpenAIProvider(GraderProvider):
    """Judge using OpenAI's GPT models.

    TODO (v0.2):
      - Initialize openai client from env (OPENAI_API_KEY).
      - Wire judge() to client.chat.completions.create.
      - Capture usage tokens, cost, latency.
    """

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None):
        self._model = model
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    def judge(self, prompt: str, *, max_tokens: int = 2048,
              temperature: float = 0.0) -> ProviderResponse:
        raise NotImplementedError("OpenAIProvider.judge — implement in v0.2")
