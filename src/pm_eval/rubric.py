"""Rubric — the structured prompt + scoring contract.

Rubrics are YAML files. Loading one returns a Rubric object that:
  1. Renders its prompt template against an input.
  2. Auto-appends a strict schema directive so judges produce parseable output.
  3. Defines the expected output structure for the Grader to parse.
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
    scale: str = "0.0-1.0"
    failure_modes: list[str] = field(default_factory=list)


@dataclass
class Rubric:
    name: str
    description: str
    input_type: str
    dimensions: list[RubricDimension]
    prompt_template: str
    output_schema: dict[str, Any]

    @classmethod
    def from_file(cls, path: str | Path) -> "Rubric":
        with open(path, "r", encoding="utf-8") as f:
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
        """Render the rubric's prompt template and append a strict schema directive.

        The schema directive forces the judge model to use the rubric's actual
        dimension names and the rubric's actual scoring scale. Without this,
        the judge invents its own structure and the parser can't extract scores.
        """
        prompt = self.prompt_template.replace("{{ input }}", input_text)
        return f"{prompt}\n\n{self._schema_directive()}"

    def _schema_directive(self) -> str:
        """Build a strict schema directive from this rubric's dimensions."""
        dim_names = [d.name for d in self.dimensions]
        dim_examples = []
        for d in self.dimensions:
            scale_hint = self._scale_hint(d.scale)
            dim_examples.append(
                f'  "{d.name}": {{ "score": {scale_hint}, '
                f'"reason": "<one-line reason>", '
                f'"failures": ["<specific failure>", "..."] }}'
            )
        schema_str = "{\n" + ",\n".join(dim_examples) + ',\n  "overall_reason": "<one paragraph aggregating across dimensions>"\n}'
        return (
            "## Required response format\n\n"
            "Respond with ONLY a single JSON object. No prose before or after. No code fences.\n\n"
            f"Use exactly these dimension keys (no renamings, no additions): "
            f"{', '.join(dim_names)}\n\n"
            "Each dimension's `score` field must use the scale specified in the rubric "
            "(numeric 0.0-1.0 for fractional dimensions, or the literal strings "
            "\"PASS\" or \"FAIL\" for binary dimensions). The `failures` array lists "
            "specific failure strings from the rubric's failure_modes, or an empty array.\n\n"
            "Schema:\n\n"
            f"{schema_str}\n\n"
            "Return only valid JSON matching this schema."
        )

    @staticmethod
    def _scale_hint(scale: str) -> str:
        scale_norm = scale.strip().upper()
        if "PASS" in scale_norm or "FAIL" in scale_norm:
            return '"PASS" or "FAIL"'
        return "0.0"  # placeholder showing it's a number
