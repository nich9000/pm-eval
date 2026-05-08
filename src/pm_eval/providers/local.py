"""Local model provider — supports Ollama and OpenAI-compatible local servers.

To use:
    from pm_eval.providers import LocalProvider
    provider = LocalProvider(model="llama3.1:8b", base_url="http://localhost:11434")

Requires `local` extra:
    pip install pm-eval[local]
"""

from pm_eval.providers.base import GraderProvider, ProviderResponse


class LocalProvider(GraderProvider):
    """Judge using a locally hosted model via Ollama or compatible API.

    TODO (v0.2):
      - Use ollama-python or generic httpx client against base_url.
      - Wire judge() to local model.
      - Cost tracking is moot for local; latency_ms still useful.
    """

    def __init__(self, model: str = "llama3.1:8b",
                 base_url: str = "http://localhost:11434"):
        self._model = model
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "local"

    @property
    def model(self) -> str:
        return self._model

    def judge(self, prompt: str, *, max_tokens: int = 2048,
              temperature: float = 0.0) -> ProviderResponse:
        raise NotImplementedError("LocalProvider.judge — implement in v0.2")
