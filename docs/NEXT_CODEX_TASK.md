# Next Codex Task: Verify and harden Slice 1

## Goal

Verify the first MarketMind commerce math engine slice and fix any issues without expanding scope.

## Required reading

- README.md
- PROJECT_BRIEF.md
- ARCHITECTURE.md
- DEVELOPMENT_PLAN.md
- TEST_PLAN.md
- APPROVAL_POLICY.md
- PNL_MODEL.md
- CODEX_HANDOFF.md
- docs/runbook.md
- docs/qa/final_audit.md

## Task

1. Install the project locally.
2. Run the unit tests.
3. Run the sample CLI.
4. Fix any test, syntax, packaging, or import errors.
5. Do not add new major features.
6. Update `docs/qa/final_audit.md` with real verification results.

## Commands

```bash
python -m venv .venv
python -m pip install -e .[dev]
python -m pytest
python -m marketmind.cli
```

## Acceptance criteria

```text
[ ] `python -m pytest` passes
[ ] `python -m marketmind.cli` prints valid JSON
[ ] no external APIs are called
[ ] no secrets are required
[ ] no live commerce actions exist
[ ] docs/qa/final_audit.md contains actual test results
```

## Scope boundary

Do not build:

- Shopify adapter
- Stripe adapter
- dashboard
- LLM agent
- product finder
- ad integration
- customer messaging

Those are later slices.
