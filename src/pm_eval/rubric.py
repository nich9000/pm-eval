"""Rubric — the structured prompt + scoring contract.

Rubrics are YAML files. Loading one returns a Rubric object that knows how to:
  1. Render its prompt template against an input (the LLM output to grade).
  2. Parse the judge's response into structured scores.
  3. Validate that the response covers all rubric dimensions.

The rubric is the contract; the model is incidental.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RubricDimension:
    """One scored dimension of a rubric, e.g. 'specificity' or 'safety'."""
    name: str
    description: str
    scale: str = "0.0-1.0"          # could also be "PASS/FAIL", "1-5", etc.
    failure_modes: list[str] = field(default_factory=list)


@dataclass
class Rubric:
    """A complete rubric loaded from YAML.

    Attributes:
      name: short identifier, e.g. 'spec-quality'
      description: one-line human description
      input_type: what kind of artifact this rubric grades (spec, summary, PRD)
      dimensions: list of RubricDimension, each scored independently
      prompt_template: Jinja-style template with {{ input }} placeholder
      output_schema: how the judge should structure its response (JSON schema-ish)
    """
    name: str
    description: str
    input_type: str
    dimensions: list[RubricDimension]
    prompt_template: str
    output_schema: dict[str, Any]

    @classmethod
    def from_file(cls, path: str | Path) -> "Rubric":
        """Load a rubric from a YAML file.

        TODO (v0.1): full schema validation, helpful errors on malformed YAML.
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(
            name=data["name"],
            description=data["description"],
            input_type=data["input_type"],
            dimensions=[RubricDimension(**d) for d in data["dimensions"]],
            prompt_template=data["prompt_template"],
            output_schema=data.get("output_schema", {}),
        )

    def render_prompt(self, input_text: str) -> str:
        """Substitute the input into the prompt template.

        TODO (v0.1): use jinja2 for proper template rendering and escaping.
        """
        return self.prompt_template.replace("{{ input }}", input_text)
