# Changelog

## v0.2.0 — 2026-07-02

- **Multi-judge consensus.** New `ConsensusGrader` grades one input with a
  panel of judges (different models, or different rubric variants) and
  surfaces disagreement as signal: per-dimension spreads, a configurable
  disagreement threshold, unanimous vs. disputed failure reconciliation,
  and judge-level parse-error isolation (one broken judge does not sink the
  panel).
- **`pm-eval consensus` CLI command** with CI-friendly exit codes:
  0 = agree, 3 = disagree, 2 = all judges errored.
- **Worked example** at `examples/multi-judge-consensus/`, including an
  offline demo that runs with zero API keys.
- **Fixed a shipped test bug:** `test_rubric_loads_yaml` asserted exact
  prompt equality and broke when v0.1 added the schema directive. The test
  now asserts the directive is present, which is the actual contract.
- 9 new consensus tests; suite is 11 passing.

## v0.1.0 — 2026-05

- Anthropic provider, robust JSON extraction, strict schema directive,
  `grade` CLI command, PRD-eval-loop worked example.
