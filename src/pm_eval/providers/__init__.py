"""Provider implementations for pm-eval.

Each provider implements the GraderProvider interface, allowing any LLM that
can take a prompt and return text to act as a judge.

Provider classes are loaded lazily so importing this module doesn't drag in
optional dependencies (e.g. `anthropic`) that the user hasn't installed.
"""

from pm_eval.providers.base import GraderProvider, ProviderResponse

__all__ = ["GraderProvider", "ProviderResponse",
           "ClaudeProvider", "OpenAIProvider", "LocalProvider"]


def __getattr__(name):
    if name == "ClaudeProvider":
        from pm_eval.providers.anthropic import ClaudeProvider
        return ClaudeProvider
    if name == "OpenAIProvider":
        from pm_eval.providers.openai import OpenAIProvider
        return OpenAIProvider
    if name == "LocalProvider":
        from pm_eval.providers.local import LocalProvider
        return LocalProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
