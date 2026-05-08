"""Tests for the Grader and Rubric components.

These tests run without an API key — they exercise the abstractions only.
Provider-level integration tests live separately and are gated behind
ANTHROPIC_API_KEY / OPENAI_API_KEY env vars.
"""

import pytest

from pm_eval.providers.base import GraderProvider, ProviderResponse
from pm_eval.rubric import Rubric


class FakeProvider(GraderProvider):
    """A canned-response provider for testing the harness without API calls."""

    def __init__(self, response_text: str = '{"score": 1.0}'):
        self._response_text = response_text

    @property
    def name(self) -> str:
        return "fake"

    @property
    def model(self) -> str:
        return "fake-model"

    def judge(self, prompt: str, *, max_tokens: int = 2048,
              temperature: float = 0.0) -> ProviderResponse:
        return ProviderResponse(text=self._response_text, model=self.model)


def test_provider_interface_minimal():
    """A FakeProvider satisfies the GraderProvider interface."""
    p = FakeProvider()
    assert p.name == "fake"
    assert p.model == "fake-model"
    response = p.judge("anything")
    assert response.text == '{"score": 1.0}'


def test_rubric_loads_yaml(tmp_path):
    """Rubric.from_file parses a minimal valid YAML rubric."""
    rubric_yaml = """
name: test-rubric
description: just for tests
input_type: test
dimensions:
  - name: dim1
    description: first dimension
prompt_template: "Grade: {{ input }}"
"""
    p = tmp_path / "test.yaml"
    p.write_text(rubric_yaml)
    r = Rubric.from_file(p)
    assert r.name == "test-rubric"
    assert len(r.dimensions) == 1
    assert "Grade: hello" == r.render_prompt("hello")


# TODO (v0.1): tests for Grader.grade once response parsing lands.
# TODO (v0.3): tests for Runner.run.
