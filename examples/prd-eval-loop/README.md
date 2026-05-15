# Worked example — PRD → Eval loop

This directory demonstrates the framework's defining claim: **the rungs work together as layers of one workflow.**

The loop:

1. **Specs rung** — generate a PRD using [`prd-generator`](https://github.com/nich9000/prd-generator).
2. **Evaluation rung** — grade that PRD using `pm-eval` against the `prd-completeness.yaml` rubric.
3. Capture both the generated artifact and the structured grade so the loop is auditable end-to-end.

## How to reproduce this run

**Prerequisites:**
- `prd-generator` installed (`pip install -e .` from that repo's root)
- `pm-eval` installed with the Anthropic extra (`pip install -e ".[anthropic]"` from this repo's root)
- `ANTHROPIC_API_KEY` set in your environment

**Step 1 — Generate a PRD:**

```bash
prd "Sellers should see at-a-glance which listings are losing rank week over week" \
    -o examples/prd-eval-loop/seller-rank-watch.md
```

**Step 2 — Grade it:**

```bash
pm-eval grade \
    -i examples/prd-eval-loop/seller-rank-watch.md \
    -r rubrics/prd-completeness.yaml \
    -o examples/prd-eval-loop/seller-rank-watch.grade.md
```

**Step 3 — Inspect the loop:**

- `seller-rank-watch.md` — the PRD produced by the Specs rung
- `seller-rank-watch.grade.md` — the structured grade produced by the Evaluation rung
- The grade scores the PRD on four dimensions (framing, story coverage, risk articulation, requirements specificity) with per-dimension scores, flagged failures, and aggregate reasoning

## What this demonstrates

Most public framework repos describe how rungs *should* fit together. This directory shows them fitting together — same author, same toolchain, two independently published artifacts evaluating each other.

It is also the basis for `pm-eval`'s v0.2 work: the single-judge grade produced here is a starting point, but the same PRD graded by Claude vs. GPT-4 vs. a local Llama model will produce different scores. The multi-judge consensus pattern is what closes that gap.

## Files in this directory

| File | Purpose |
|---|---|
| `seller-rank-watch.md` | Generated PRD (run Step 1 to produce) |
| `seller-rank-watch.grade.md` | Markdown grade output (run Step 2 to produce) |
| `seller-rank-watch.grade.json` | Optional JSON grade output (add `--format json` to Step 2) |
