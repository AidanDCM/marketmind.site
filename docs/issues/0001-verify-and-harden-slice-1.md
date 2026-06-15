# Issue Draft: Verify and harden Slice 1

## Title

Verify and harden MarketMind commerce math engine

## Body

MarketMind now has its first real engineering slice: a local Python commerce math engine with schemas, rules, CLI dry run, and unit tests.

### Goal

Verify the implementation locally and fix only issues needed to make Slice 1 pass.

### Required commands

```bash
python -m venv .venv
python -m pip install -e .[dev]
python -m pytest
python -m marketmind.cli
```

### Acceptance criteria

```text
[ ] tests pass
[ ] sample CLI prints valid JSON
[ ] no external APIs are called
[ ] no secrets are needed
[ ] no live commerce actions exist
[ ] docs/qa/final_audit.md is updated with actual verification results
```

### Scope boundary

Do not add Shopify, Stripe, ads, dashboard, LLM agent, product finder, or messaging in this issue.

### Next issue after this

Build product/opportunity schemas and explainable scoring.
