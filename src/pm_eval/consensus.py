"""Consensus — grade one input with multiple judges and surface disagreement as signal.

The core idea: a single judge model gives you a score. A panel of judges gives
you a score AND a confidence signal. When two judges built from different
models (or different prompt variants) agree, you can trust the grade more.
When they disagree, the disagreement itself is the finding — it marks exactly
the dimensions where the rubric is ambiguous, the artifact is borderline, or
one judge model has a blind spot. Those are the places a human should look.

Two supported panel shapes:
  1. Same rubric, different judge models  (model disagreement)
  2. Same judge model, different rubrics  (prompt/rubric disagreement)
Or any mix — a judge is just a labeled Grader.

Usage:
    from pm_eval import ConsensusGrader
    from pm_eval.grader import Grader
    from pm_eval.providers import ClaudeProvider

    panel = ConsensusGrader({
        "sonnet": Grader(ClaudeProvider(model="claude-sonnet-4-6"), "rubrics/spec-quality.yaml"),
        "haiku":  Grader(ClaudeProvider(model="claude-haiku-4-5-20251001"), "rubrics/spec-quality.yaml"),
    })
    result = panel.grade(spec_text)
    print(result.consensus_score)   # mean across judges
    print(result.disagreements)     # dimensions where judges split
"""

from dataclasses import dataclass, field

from pm_eval.grader import GradeResult, Grader

# A dimension whose per-judge scores spread wider than this is flagged as a
# disagreement. 0.25 on a 0-1 scale means "one judge saw a materially
# different artifact than the other" — tight enough to catch real splits,
# loose enough to ignore rounding-level noise.
DEFAULT_DISAGREEMENT_THRESHOLD = 0.25


@dataclass
class Disagreement:
    """One dimension the judges could not agree on."""
    dimension: str
    spread: float                       # max - min across judges
    scores: dict[str, float]            # judge label -> score

    def to_dict(self) -> dict:
        return {"dimension": self.dimension, "spread": round(self.spread, 4),
                "scores": self.scores}


@dataclass
class ConsensusResult:
    """Aggregated verdict from a panel of judges.

    The two headline fields:
      - consensus_score: mean overall score across judges that parsed cleanly.
      - disagreements: the signal. Empty list = the judges agree and the
        score is trustworthy. Non-empty = a human should look at exactly
        these dimensions before trusting the grade.
    """
    consensus_score: float
    score_spread: float                            # max - min of judge overall scores
    results: dict[str, GradeResult] = field(default_factory=dict)
    dimension_stats: dict[str, dict] = field(default_factory=dict)
    disagreements: list[Disagreement] = field(default_factory=list)
    unanimous_failures: list[str] = field(default_factory=list)   # every judge flagged it
    disputed_failures: dict[str, list[str]] = field(default_factory=dict)  # failure -> judges who flagged it
    errored_judges: dict[str, str] = field(default_factory=dict)  # label -> parse_error
    threshold: float = DEFAULT_DISAGREEMENT_THRESHOLD
    total_cost_usd: float | None = None

    @property
    def agreement(self) -> bool:
        """True when no dimension exceeded the disagreement threshold."""
        return not self.disagreements

    def to_dict(self) -> dict:
        return {
            "consensus_score": round(self.consensus_score, 4),
            "score_spread": round(self.score_spread, 4),
            "agreement": self.agreement,
            "threshold": self.threshold,
            "judges": {label: r.to_dict() for label, r in self.results.items()},
            "dimension_stats": self.dimension_stats,
            "disagreements": [d.to_dict() for d in self.disagreements],
            "unanimous_failures": self.unanimous_failures,
            "disputed_failures": self.disputed_failures,
            "errored_judges": self.errored_judges,
            "total_cost_usd": self.total_cost_usd,
        }

    def to_markdown(self) -> str:
        lines = ["# Consensus Grade", ""]
        verdict = "AGREEMENT" if self.agreement else "DISAGREEMENT"
        lines.append(f"- **Verdict:** {verdict}")
        lines.append(f"- **Consensus score:** {self.consensus_score:.2f} "
                     f"(spread {self.score_spread:.2f} across {len(self.results)} judges)")
        if self.total_cost_usd is not None:
            lines.append(f"- **Total cost:** ${self.total_cost_usd:.4f}")
        lines.append("")

        lines.append("## Judges")
        lines.append("")
        lines.append("| Judge | Overall | " + " | ".join(self.dimension_stats.keys()) + " |")
        lines.append("|---|---|" + "---|" * len(self.dimension_stats))
        for label, r in self.results.items():
            dims = " | ".join(f"{r.dimensions.get(d, float('nan')):.2f}"
                              for d in self.dimension_stats)
            lines.append(f"| {label} | {r.score:.2f} | {dims} |")
        lines.append("")

        if self.disagreements:
            lines.append("## Where the judges disagree (review these by hand)")
            lines.append("")
            for d in sorted(self.disagreements, key=lambda x: -x.spread):
                per_judge = ", ".join(f"{k}={v:.2f}" for k, v in d.scores.items())
                lines.append(f"- **{d.dimension}** — spread {d.spread:.2f} ({per_judge})")
            lines.append("")
            lines.append("Disagreement is signal, not noise. These dimensions are where "
                         "the rubric is ambiguous, the artifact is borderline, or one "
                         "judge has a blind spot. A single-judge run would have hidden this.")
            lines.append("")

        if self.unanimous_failures:
            lines.append("## Failures every judge flagged (high confidence)")
            lines.append("")
            for f in self.unanimous_failures:
                lines.append(f"- {f}")
            lines.append("")

        if self.disputed_failures:
            lines.append("## Failures only some judges flagged (verify)")
            lines.append("")
            for failure, judges in self.disputed_failures.items():
                lines.append(f"- {failure} _(flagged by: {', '.join(judges)})_")
            lines.append("")

        if self.errored_judges:
            lines.append("## Judges excluded (parse errors)")
            lines.append("")
            for label, err in self.errored_judges.items():
                first_line = err.splitlines()[0] if err else "unknown error"
                lines.append(f"- **{label}**: {first_line}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


class ConsensusGrader:
    """Run the same input past a panel of judges and reconcile the grades.

    `judges` maps a human-readable label to a configured Grader. Labels appear
    in reports, so name them after what varies: "sonnet"/"haiku" for a model
    panel, "strict-rubric"/"lenient-rubric" for a prompt panel.
    """

    def __init__(self, judges: dict[str, Grader],
                 *, disagreement_threshold: float = DEFAULT_DISAGREEMENT_THRESHOLD):
        if len(judges) < 2:
            raise ValueError("A consensus panel needs at least 2 judges; "
                             f"got {len(judges)}. Use Grader directly for one judge.")
        self._judges = judges
        self._threshold = disagreement_threshold

    def grade(self, input_text: str, **context) -> ConsensusResult:
        results: dict[str, GradeResult] = {}
        for label, grader in self._judges.items():
            results[label] = grader.grade(input_text, **context)

        valid = {label: r for label, r in results.items() if not r.parse_error}
        errored = {label: r.parse_error for label, r in results.items() if r.parse_error}

        if not valid:
            return ConsensusResult(
                consensus_score=0.0, score_spread=0.0, results=results,
                errored_judges=errored, threshold=self._threshold,
                total_cost_usd=self._total_cost(results),
            )

        overall_scores = [r.score for r in valid.values()]
        consensus_score = sum(overall_scores) / len(overall_scores)
        score_spread = max(overall_scores) - min(overall_scores)

        # Per-dimension stats across the judges that share the dimension.
        all_dims: list[str] = []
        for r in valid.values():
            for d in r.dimensions:
                if d not in all_dims:
                    all_dims.append(d)

        dimension_stats: dict[str, dict] = {}
        disagreements: list[Disagreement] = []
        for dim in all_dims:
            scores = {label: r.dimensions[dim]
                      for label, r in valid.items() if dim in r.dimensions}
            if not scores:
                continue
            values = list(scores.values())
            spread = max(values) - min(values)
            dimension_stats[dim] = {
                "mean": round(sum(values) / len(values), 4),
                "min": min(values),
                "max": max(values),
                "spread": round(spread, 4),
                "scores": scores,
            }
            if len(scores) >= 2 and spread >= self._threshold:
                disagreements.append(Disagreement(dimension=dim, spread=spread,
                                                  scores=scores))

        # Failure reconciliation: unanimous failures are high-confidence
        # findings; failures only some judges saw need human verification.
        failure_sets = {label: set(r.failures) for label, r in valid.items()}
        unanimous: list[str] = []
        disputed: dict[str, list[str]] = {}
        seen: set[str] = set()
        for label, r in valid.items():
            for f in r.failures:
                if f in seen:
                    continue
                seen.add(f)
                flagged_by = [lbl for lbl, fs in failure_sets.items() if f in fs]
                if len(flagged_by) == len(valid):
                    unanimous.append(f)
                else:
                    disputed[f] = flagged_by

        return ConsensusResult(
            consensus_score=consensus_score,
            score_spread=score_spread,
            results=results,
            dimension_stats=dimension_stats,
            disagreements=disagreements,
            unanimous_failures=unanimous,
            disputed_failures=disputed,
            errored_judges=errored,
            threshold=self._threshold,
            total_cost_usd=self._total_cost(results),
        )

    @staticmethod
    def _total_cost(results: dict[str, GradeResult]) -> float | None:
        costs = [r.cost_usd for r in results.values() if r.cost_usd is not None]
        return round(sum(costs), 6) if costs else None
