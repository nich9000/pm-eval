"""Provider implementations for pm-eval.

Each provider implements the GraderProvider interface, allowing any LLM that
can take a prompt and return text to act as a judge. Adding a new provider
means implementing a single interface — no changes to grader.py, rubric.py,
or any rubric file.
"""

from pm_eval.providers.base import GraderProvider

__all__ = ["GraderProvider"]
