# MarketMind Autopilot Runbook

## Current status

The repo now contains:

- static public landing page
- project brief
- architecture
- development plan
- test plan
- approval policy
- P&L model
- Codex handoff
- first Python commerce math engine slice

## Local setup

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell may use: .venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

## Run tests

```bash
python -m pytest
```

## Run sample calculation

```bash
python -m marketmind.cli
```

Expected behavior:

- prints JSON unit economics for the Daily Driver Interior Refresh Kit
- does not call external APIs
- does not use secrets
- does not create real commerce actions

## Release checklist

Before calling the current repo baseline ready:

```text
[ ] Static site loads locally
[ ] README links all planning docs
[ ] pytest passes
[ ] sample CLI prints JSON
[ ] no secrets committed
[ ] .env.example contains no real credentials
[ ] Codex handoff is clear
```

## First defect response

If tests fail:

1. Do not continue to new slices.
2. Fix the failing test or revert the slice.
3. Add a regression test if the failure revealed a missing case.
4. Document the issue in the completion report.

## Next slice after math engine

Build the product/opportunity schema and explainable scoring engine.
