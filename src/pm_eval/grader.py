"""Grader — the orchestrator that ties a provider, a rubric, and an input together.

Usage:
    from pm_eval import Grader
    from pm_eval.providers import ClaudeProvider

    grader = Grader(
        provider=ClaudeProvider(),
        rubric="rubrics/spec-quality.yaml"
    )
    result = grader.grade(open("examples/sample_spec.md").read())
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pm_eval.providers.base import GraderProvider, ProviderResponse
from pm_eval.rubric import Rubric


@dataclass
class GradeResult:
    """The structured output of a single grading run."""
    score: float                                         # overall, normalized 0.0-1.0
    dimensions: dict[str, float] = field(default_factory=dict)   # per-dimension scores
    failures: list[str] = field(default_factory=list)    # rubric failure modes hit
    reasoning: str = ""                                  # judge's explanation
    raw_response: ProviderResponse | None = None         # for debugging
    rubric_name: str = ""
    provider_name: str = ""


class Grader:
    """Apply a rubric to LLM/agent output, using a swappable judge provider."""

    def __init__(self, provider: GraderProvider, rubric: str | Path | Rubric):
        self._provider = provider
        if isinstance(rubric, Rubric):
            self._rubric = rubric
        else:
            self._rubric = Rubric.from_file(rubric)

    def grade(self, input_text: str) -> GradeResult:
        """Grade a single input against the configured rubric.

        Pipeline:
          1. Render the rubric's prompt template against the input.
          2. Hand the prompt to the provider's judge() method.
          3. Parse the response into a GradeResult.

        TODO (v0.1):
          - Implement response parsing (likely JSON-extraction with fallback).
          - Validate that all rubric dimensions are present in the response.
          - Aggregate dimension scores into overall score per rubric weighting.
        """
        prompt = self._rubric.render_prompt(input_text)
        response = self._provider.judge(prompt)
        # TODO: parse response.text into structured GradeResult
        return GradeResult(
            score=0.0,
            raw_response=response,
            rubric_name=self._rubric.name,
            provider_name=self._provider.name,
        )
