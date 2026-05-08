"""GraderProvider — the provider-agnostic interface.

Any LLM that can take a prompt and return text can be a judge. To add a new
provider (Gemini, Mistral, a custom hosted model, anything), implement this
interface and you're done. Nothing else in pm-eval needs to change.

This is the load-bearing abstraction of the whole library. Keep it stable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderResponse:
    """The raw response from a judge provider before pm-eval parses it."""
    text: str
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[int] = None


class GraderProvider(ABC):
    """Abstract base class for judge-model providers.

    Implementations must:
      1. Accept a prompt string in `judge()`.
      2. Return a ProviderResponse with the model's text output.
      3. Be configurable per-instance (model name, temperature, etc.).

    Implementations should NOT:
      - Parse the response into scores. That's the rubric's job.
      - Make assumptions about the rubric format. The provider is dumb;
        the runner is smart.
      - Cache results. Caching belongs at the runner layer.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """A short identifier for this provider, e.g. 'anthropic', 'openai'."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model(self) -> str:
        """The specific model in use, e.g. 'claude-sonnet-4-6'."""
        raise NotImplementedError

    @abstractmethod
    def judge(self, prompt: str, *, max_tokens: int = 2048,
              temperature: float = 0.0) -> ProviderResponse:
        """Send a prompt to the judge model and return its response.

        Implementations should default to deterministic settings (temperature=0)
        so eval runs are reproducible.
        """
        raise NotImplementedError
