"""Offline demo of ConsensusGrader — runs with zero API keys.

Replays two realistic judge responses (a strict judge and a lenient judge)
grading the same PRD against the prd-completeness rubric, so you can see the
disagreement report without spending tokens. Swap in real providers for a
live run; see README.md in this folder.

Run from the repo root:
    python examples/multi-judge-consensus/demo_offline.py
"""

import json
from pathlib import Path

from pm_eval.consensus import ConsensusGrader
from pm_eval.grader import Grader
from pm_eval.providers.base import GraderProvider, ProviderResponse

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC = REPO_ROOT / "rubrics" / "prd-completeness.yaml"
PRD = REPO_ROOT / "examples" / "prd-eval-loop" / "ai-shopping-assistant.md"


class ReplayProvider(GraderProvider):
    """Returns a canned judge response. Stands in for a real model."""

    def __init__(self, payload: dict, model_name: str):
        self._payload, self._model_name = payload, model_name

    @property
    def name(self) -> str:
        return "replay"

    @property
    def model(self) -> str:
        return self._model_name

    def judge(self, prompt, *, max_tokens=2048, temperature=0.0):
        return ProviderResponse(text=json.dumps(self._payload), model=self._model_name)


# What a stricter judge and a more lenient judge typically return for the
# same borderline PRD. The split on `risks` is the interesting part.
STRICT = {
    "framing": {"score": 0.9, "reason": "Clear problem and audience.", "failures": []},
    "story_coverage": {"score": 0.85, "reason": "Stories are concrete.", "failures": []},
    "requirements_specificity": {"score": 0.8, "reason": "Mostly testable.", "failures": []},
    "risk_articulation": {"score": 0.35,
                          "reason": "Compliance risks named but unquantified; no mitigation owners.",
                          "failures": ["risk without named mitigation owner"]},
    "overall_reason": "Solid structure, but the risk section would not survive legal review.",
}
LENIENT = {
    "framing": {"score": 0.95, "reason": "Well framed.", "failures": []},
    "story_coverage": {"score": 0.9, "reason": "Good coverage.", "failures": []},
    "requirements_specificity": {"score": 0.85, "reason": "Testable.", "failures": []},
    "risk_articulation": {"score": 0.8,
                          "reason": "Risks identified, which is more than most PRDs do.",
                          "failures": []},
    "overall_reason": "Ship it; risks are identified even if not fully mitigated.",
}


def main():
    panel = ConsensusGrader({
        "strict-judge": Grader(ReplayProvider(STRICT, "strict-model"), RUBRIC),
        "lenient-judge": Grader(ReplayProvider(LENIENT, "lenient-model"), RUBRIC),
    })
    result = panel.grade(PRD.read_text(encoding="utf-8"))

    out = Path(__file__).parent / "consensus-report.md"
    out.write_text(result.to_markdown(), encoding="utf-8")
    print(result.to_markdown())
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
