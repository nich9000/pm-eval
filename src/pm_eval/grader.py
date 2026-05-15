"""Grader — orchestrates provider + rubric + input into a structured result.

Usage:
    from pm_eval import Grader
    from pm_eval.providers import ClaudeProvider

    grader = Grader(provider=ClaudeProvider(), rubric="rubrics/spec-quality.yaml")
    result = grader.grade(open("examples/sample_spec.md").read())
    print(result.to_markdown())
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from pm_eval.providers.base import GraderProvider, ProviderResponse
from pm_eval.rubric import Rubric


@dataclass
class GradeResult:
    """Structured output of a single grading run."""
    score: float                                          # overall, 0.0-1.0
    dimensions: dict[str, float] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    reasoning: str = ""
    raw_response: ProviderResponse | None = None
    rubric_name: str = ""
    provider_name: str = ""
    cost_usd: float | None = None
    latency_ms: int | None = None
    parse_error: str | None = None

    def to_markdown(self) -> str:
        lines = [f"# Grade Result — {self.rubric_name}", ""]
        lines.append(f"- **Overall score:** {self.score:.2f}")
        if self.raw_response:
            lines.append(f"- **Provider:** {self.provider_name} / {self.raw_response.model}")
        if self.cost_usd is not None:
            lines.append(f"- **Cost:** ${self.cost_usd:.4f}")
        if self.latency_ms is not None:
            lines.append(f"- **Latency:** {self.latency_ms} ms")
        lines.append("")
        if self.dimensions:
            lines.append("## Dimensions")
            for dim, score in self.dimensions.items():
                lines.append(f"- **{dim}:** {score:.2f}")
            lines.append("")
        if self.failures:
            lines.append("## Failures flagged")
            for fail in self.failures:
                lines.append(f"- {fail}")
            lines.append("")
        if self.reasoning:
            lines.append("## Reasoning")
            lines.append(self.reasoning)
            lines.append("")
        if self.parse_error:
            lines.append("## Parse error")
            lines.append(f"```\n{self.parse_error}\n```")
        return "\n".join(lines).rstrip() + "\n"

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "dimensions": self.dimensions,
            "failures": self.failures,
            "reasoning": self.reasoning,
            "rubric_name": self.rubric_name,
            "provider_name": self.provider_name,
            "model": self.raw_response.model if self.raw_response else None,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "parse_error": self.parse_error,
        }


def _extract_json(text: str) -> dict:
    """Robustly extract a JSON object from the judge model's response.

    Handles three common patterns:
      1. Bare JSON object (best case).
      2. JSON wrapped in a ```json ... ``` fenced block.
      3. JSON with prose before/after.
    """
    text = text.strip()
    # Pattern 2: fenced code block
    fence = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        return json.loads(fence.group(1))
    # Pattern 1 & 3: find the largest balanced { ... }
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("Unbalanced JSON braces in response")


def _coerce_score(raw) -> float:
    """Accept 0.0-1.0 floats, ints, or PASS/FAIL strings."""
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        upper = raw.strip().upper()
        if upper == "PASS":
            return 1.0
        if upper == "FAIL":
            return 0.0
        try:
            return float(upper)
        except ValueError:
            return 0.0
    return 0.0


class Grader:
    """Apply a rubric to LLM/agent output using a swappable judge provider."""

    def __init__(self, provider: GraderProvider, rubric: str | Path | Rubric):
        self._provider = provider
        self._rubric = rubric if isinstance(rubric, Rubric) else Rubric.from_file(rubric)

    def grade(self, input_text: str, **context) -> GradeResult:
        """Grade a single input against the configured rubric.

        Extra keyword arguments are substituted into the rubric prompt template
        as {{ key }} placeholders, alongside the default {{ input }}.
        """
        prompt = self._rubric.render_prompt(input_text)
        # Allow multi-key prompt templates (e.g., {{ source }} for summary-fidelity)
        for key, value in context.items():
            prompt = prompt.replace(f"{{{{ {key} }}}}", str(value))

        response = self._provider.judge(prompt)

        try:
            parsed = _extract_json(response.text)
        except (ValueError, json.JSONDecodeError) as exc:
            return GradeResult(
                score=0.0,
                failures=[],
                reasoning="",
                raw_response=response,
                rubric_name=self._rubric.name,
                provider_name=self._provider.name,
                cost_usd=response.cost_usd,
                latency_ms=response.latency_ms,
                parse_error=f"{type(exc).__name__}: {exc}\n\nRaw response:\n{response.text[:500]}",
            )

        dimensions: dict[str, float] = {}
        failures: list[str] = []
        for dim in self._rubric.dimensions:
            data = parsed.get(dim.name, {})
            if isinstance(data, dict):
                dimensions[dim.name] = _coerce_score(data.get("score", 0.0))
                dim_failures = data.get("failures") or []
                if isinstance(dim_failures, list):
                    failures.extend(str(f) for f in dim_failures)
            else:
                dimensions[dim.name] = _coerce_score(data)

        overall = sum(dimensions.values()) / len(dimensions) if dimensions else 0.0
        reasoning = parsed.get("overall_reason") or parsed.get("reasoning") or ""

        return GradeResult(
            score=overall,
            dimensions=dimensions,
            failures=failures,
            reasoning=reasoning,
            raw_response=response,
            rubric_name=self._rubric.name,
            provider_name=self._provider.name,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
        )
