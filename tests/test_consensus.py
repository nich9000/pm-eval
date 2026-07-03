"""Tests for ConsensusGrader — all offline, no API keys required."""

import json

import pytest

from pm_eval.consensus import ConsensusGrader, DEFAULT_DISAGREEMENT_THRESHOLD
from pm_eval.grader import Grader
from pm_eval.providers.base import GraderProvider, ProviderResponse
from pm_eval.rubric import Rubric


RUBRIC_YAML = """
name: test-rubric
description: consensus test rubric
input_type: test
dimensions:
  - name: clarity
    description: is it clear
  - name: completeness
    description: is it complete
prompt_template: "Grade this: {{ input }}"
"""


class CannedProvider(GraderProvider):
    """Returns a fixed judge response, so panels are fully deterministic."""

    def __init__(self, payload: dict, model_name: str = "canned-model"):
        self._payload = payload
        self._model_name = model_name

    @property
    def name(self) -> str:
        return "canned"

    @property
    def model(self) -> str:
        return self._model_name

    def judge(self, prompt: str, *, max_tokens: int = 2048,
              temperature: float = 0.0) -> ProviderResponse:
        return ProviderResponse(text=json.dumps(self._payload), model=self._model_name)


def _rubric(tmp_path):
    p = tmp_path / "rubric.yaml"
    p.write_text(RUBRIC_YAML)
    return Rubric.from_file(p)


def _judge(tmp_path, clarity, completeness, failures=None):
    payload = {
        "clarity": {"score": clarity, "reason": "r", "failures": failures or []},
        "completeness": {"score": completeness, "reason": "r", "failures": []},
        "overall_reason": "test",
    }
    return Grader(provider=CannedProvider(payload), rubric=_rubric(tmp_path))


def test_panel_requires_two_judges(tmp_path):
    with pytest.raises(ValueError):
        ConsensusGrader({"only": _judge(tmp_path, 1.0, 1.0)})


def test_agreement_panel(tmp_path):
    panel = ConsensusGrader({
        "judge-a": _judge(tmp_path, 0.9, 0.8),
        "judge-b": _judge(tmp_path, 0.85, 0.8),
    })
    result = panel.grade("anything")
    assert result.agreement
    assert result.disagreements == []
    assert result.consensus_score == pytest.approx((0.85 + 0.825) / 2)
    assert result.score_spread == pytest.approx(0.025)
    assert result.dimension_stats["clarity"]["spread"] == pytest.approx(0.05)


def test_disagreement_is_flagged(tmp_path):
    panel = ConsensusGrader({
        "strict": _judge(tmp_path, 0.9, 0.3),
        "lenient": _judge(tmp_path, 0.9, 0.9),
    })
    result = panel.grade("anything")
    assert not result.agreement
    assert len(result.disagreements) == 1
    d = result.disagreements[0]
    assert d.dimension == "completeness"
    assert d.spread == pytest.approx(0.6)
    assert d.scores == {"strict": 0.3, "lenient": 0.9}


def test_threshold_is_configurable(tmp_path):
    judges = {
        "a": _judge(tmp_path, 0.9, 0.7),
        "b": _judge(tmp_path, 0.9, 0.9),
    }
    default_panel = ConsensusGrader(dict(judges))
    assert default_panel.grade("x").agreement  # 0.2 < 0.25 default

    tight_panel = ConsensusGrader(dict(judges), disagreement_threshold=0.15)
    assert not tight_panel.grade("x").agreement  # 0.2 >= 0.15


def test_failure_reconciliation(tmp_path):
    panel = ConsensusGrader({
        "a": _judge(tmp_path, 0.9, 0.9, failures=["missing acceptance criteria", "vague owner"]),
        "b": _judge(tmp_path, 0.9, 0.9, failures=["missing acceptance criteria"]),
    })
    result = panel.grade("anything")
    assert result.unanimous_failures == ["missing acceptance criteria"]
    assert result.disputed_failures == {"vague owner": ["a"]}


def test_parse_error_judge_is_excluded_not_fatal(tmp_path):
    class BrokenProvider(CannedProvider):
        def judge(self, prompt, *, max_tokens=2048, temperature=0.0):
            return ProviderResponse(text="not json at all", model="broken")

    broken = Grader(provider=BrokenProvider({}), rubric=_rubric(tmp_path))
    panel = ConsensusGrader({
        "good-a": _judge(tmp_path, 0.8, 0.8),
        "good-b": _judge(tmp_path, 0.8, 0.8),
        "broken": broken,
    })
    result = panel.grade("anything")
    assert "broken" in result.errored_judges
    assert result.consensus_score == pytest.approx(0.8)
    assert result.agreement


def test_all_judges_errored(tmp_path):
    class BrokenProvider(CannedProvider):
        def judge(self, prompt, *, max_tokens=2048, temperature=0.0):
            return ProviderResponse(text="garbage", model="broken")

    broken_a = Grader(provider=BrokenProvider({}), rubric=_rubric(tmp_path))
    broken_b = Grader(provider=BrokenProvider({}), rubric=_rubric(tmp_path))
    result = ConsensusGrader({"a": broken_a, "b": broken_b}).grade("x")
    assert result.consensus_score == 0.0
    assert len(result.errored_judges) == 2


def test_markdown_report_contains_signal_framing(tmp_path):
    panel = ConsensusGrader({
        "strict": _judge(tmp_path, 0.9, 0.3),
        "lenient": _judge(tmp_path, 0.9, 0.9),
    })
    md = panel.grade("anything").to_markdown()
    assert "DISAGREEMENT" in md
    assert "completeness" in md
    assert "Disagreement is signal, not noise." in md


def test_to_dict_round_trips_to_json(tmp_path):
    panel = ConsensusGrader({
        "a": _judge(tmp_path, 0.9, 0.8),
        "b": _judge(tmp_path, 0.7, 0.8),
    })
    payload = panel.grade("anything").to_dict()
    text = json.dumps(payload)  # must be JSON-serializable
    assert json.loads(text)["agreement"] is False or json.loads(text)["agreement"] is True
