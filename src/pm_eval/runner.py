"""Runner — apply a rubric to many outputs at scale, track regression over time.

The Runner is what turns a one-off grade into a regression suite. It batches
inputs, parallelizes calls, persists results, and surfaces drift between runs.

TODO (v0.3):
  - Batch grading with concurrency limit.
  - Persist results to JSON-lines per run.
  - Diff runs to flag regressions.
  - Cost tracking aggregated across runs.
"""

from dataclasses import dataclass
from pathlib import Path

from pm_eval.grader import Grader, GradeResult


@dataclass
class SuiteResult:
    """Aggregated result of running a rubric across many inputs."""
    rubric_name: str
    provider_name: str
    total: int
    passed: int
    failed: int
    average_score: float
    individual: list[GradeResult]


class Runner:
    """Run a grader over a directory of inputs, output a SuiteResult."""

    def __init__(self, grader: Grader):
        self._grader = grader

    def run(self, inputs_dir: str | Path, *, glob: str = "*.md") -> SuiteResult:
        """Grade every file matching glob in inputs_dir.

        TODO (v0.3): implement.
        """
        raise NotImplementedError("Runner.run — implement in v0.3")
