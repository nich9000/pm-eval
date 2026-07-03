# Multi-judge consensus — worked example

One judge gives you a score. A panel gives you a score plus a confidence
signal. This example grades the same PRD with two judges and shows how
`pm-eval` surfaces their disagreement as the finding.

## Offline demo (no API keys)

```bash
python examples/multi-judge-consensus/demo_offline.py
```

Replays a strict judge and a lenient judge grading
`examples/prd-eval-loop/ai-shopping-assistant.md`. They agree on framing,
story coverage, and requirements specificity. They split hard on
`risk_articulation` (0.35 vs 0.80, spread 0.45). The report flags exactly that dimension
for human review. See the generated [consensus-report.md](consensus-report.md).

A single-judge run would have returned either 0.73 or 0.88 and hidden the
split entirely. That is the point.

## Live run (two Claude models as judges)

```bash
export ANTHROPIC_API_KEY=...
pm-eval consensus \
  --input examples/prd-eval-loop/ai-shopping-assistant.md \
  --rubric rubrics/prd-completeness.yaml \
  -j anthropic:claude-sonnet-4-6 \
  -j anthropic:claude-haiku-4-5-20251001
```

Exit codes make it CI-friendly: `0` = judges agree, `3` = judges disagree
(gate merges on it, or route to human review), `2` = every judge errored.

## Prompt-variant panels

Judges do not have to differ by model. The Python API takes any labeled
`Grader`, so two rubric variants with the same model form a panel too:

```python
from pm_eval import ConsensusGrader, Grader
from pm_eval.providers import ClaudeProvider

panel = ConsensusGrader({
    "strict-rubric": Grader(ClaudeProvider(), "rubrics/spec-quality-strict.yaml"),
    "lenient-rubric": Grader(ClaudeProvider(), "rubrics/spec-quality.yaml"),
})
```

If the two rubric phrasings produce different grades for the same artifact,
your rubric is ambiguous. That is a rubric bug, and this is how you find it.
