# Changelog

All notable changes to MarketMind Autopilot are recorded here.
Format: each entry has a date, a type (Added / Changed / Fixed / Removed), and a short description.
This file is part of the Parts & Pieces starter package requirement.

---

## 2026-06-15 — Slice 4: Experiment rule engine

### Added
- `ExperimentSnapshot` schema: captures live test performance counters
  (visits, orders, ad spend, ATC, refunds, shipping). Derived properties
  (actual_cac, conversion_rate, add_to_cart_rate, refund_rate, shipping_overrun)
  computed from raw counters, never stored.
- `ExperimentRuling` + `ExperimentRulingResult` schemas.
- `marketmind/experiment_rules.py`: `evaluate_experiment()` applies PNL_MODEL
  kill/scale rules in strict priority — kill → pause → revise → scale → continue.
  Scale always sets `requires_approval=True`.
- Slice 4 kill/scale thresholds added to `rules.py`.
- 13 new tests in `tests/test_experiment_rules.py`.

### Fixed
- Duplicate `NICHE_SCORE_WEIGHTS` block in `rules.py` removed.

---

## 2026-06-15 — Slice 2: Scoring engine + Slice 1 hardening + Credential docs

### Added
- Slice 2 scoring engine (`marketmind/scoring.py`): `score_product`,
  `score_niche`, `classify_assumption`, `recommend_channel`.
  Explainable per-criterion breakdown; confidence capped by evidence quality.
  Unsourced claims can never be `VERIFIED`.
- Channel ladder: Stripe Payment Link → eBay/TikTok → Shopify → Amazon-later
  → do-not-sell.
- Scoring schemas: `ProductCandidate`, `NicheCandidate`, `AssumptionRecord`,
  `Channel`, `ChannelRecommendation`, `CriterionScore`, `ScoreResult`,
  `ScoreVerdict`, `AssumptionStatus`.
- Scoring weights/thresholds in `rules.py`.
- `score-sample` CLI command.
- 15 new tests in `tests/test_scoring.py`.
- `docs/API_KEYS_AND_CREDENTIALS.md`: sandbox-first, read-only-first,
  least-privilege credential setup guide (no real secrets).
- `ruff>=0.6` pinned in dev deps; `[tool.ruff]` config added to `pyproject.toml`.
- `*.egg-info/`, `build/`, `dist/` added to `.gitignore`.

### Fixed
- Rule-ordering bug: thin-margin + losing-after-ads product now correctly returns
  `REVISE_OFFER` (engine was right; the original test expectation was wrong).
- Long line in `math_engine.py` wrapped to satisfy E501.
- Test renamed to `test_thin_margin_losing_after_ads_revises_offer`.

### Changed
- `.env.example` upgraded to restricted-key model (Stripe restricted keys,
  `SHOPIFY_API_VERSION`, eBay sandbox OAuth, Amazon SP-API, ad-platform read-only).
- README: new credential doc linked.

---

## 2026-06-15 — Slice 1: Commerce math engine (initial build)

### Added
- Python package scaffold: `marketmind/`, `tests/`, `pyproject.toml`.
- `ProductCostInput` and `UnitEconomicsResult` schemas (`schemas.py`).
- `calculate_unit_economics()` engine (`math_engine.py`).
- Kill/scale business rules (`rules.py`).
- CLI dry-run sample (`cli.py`).
- 7 unit tests (`tests/test_math_engine.py`).
- `.env.example`, `.gitignore`, initial planning docs.
