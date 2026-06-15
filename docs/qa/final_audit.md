# MarketMind Initial QA Audit

## Date

2026-06-15

## Scope

This audit covers the repo upgrade from a simple static page into a build-ready MarketMind Autopilot baseline.

## Completed

```text
[x] README upgraded
[x] Landing page repositioned
[x] Project brief added
[x] Architecture document added
[x] Development plan added
[x] Test plan added
[x] Approval policy added
[x] P&L model added
[x] Codex handoff added
[x] .env.example added with no real secrets
[x] ADR-0001 added
[x] Runbook added
[x] Python project config added
[x] marketmind package scaffold added
[x] Commerce math engine added
[x] CLI dry-run sample added
[x] Unit tests added
```

## Not verified in this session

```text
[ ] Static page previewed locally
[ ] GitHub Pages deployment checked
```

## Verification run 2026-06-15 (Slice 1 harden)

Environment: Windows 11, Python 3.14.5, ruff 0.15.13.

```text
[x] python -m pip install -e .[dev]    -> clean install
[x] python -m pytest                   -> 8 passed
[x] python -m marketmind.cli           -> valid JSON (paid_test_requires_approval)
[x] python -m ruff check .             -> All checks passed
```

Bug found and fixed: `_recommend_action` returns REVISE_OFFER (not PAUSE_ADS)
for a product that is both thin-margin (<25% gross) and losing after ads. The
engine was correct; the original test encoded the wrong expectation. Decision:
a structurally thin margin cannot be rescued by lowering CAC, so REVISE_OFFER is
the honest signal — the `risks` array still names `estimated_cac_makes_offer_unprofitable`,
so the CAC problem is not hidden. Test renamed to
`test_thin_margin_losing_after_ads_revises_offer` and a new
`test_healthy_margin_but_cac_too_high_pauses_ads` was added so the PAUSE_ADS path
stays covered.

Also: pinned `ruff>=0.6` in dev deps, added `[tool.ruff]` config (line-length
100, lint select E/F/I/UP/B), and rewrapped one long line in `math_engine.py`.

Credential documentation added: `docs/API_KEYS_AND_CREDENTIALS.md` (sandbox-first,
read-only-first, least-privilege, approval-gated) and `.env.example` upgraded to
the restricted-key model (Stripe restricted keys, Shopify API version, eBay
sandbox OAuth, Amazon SP-API, ad-platform read-only placeholders). No real
secrets introduced.

## Verification run 2026-06-15 (Slice 2 scoring engine)

Added the explainable scoring engine (DEVELOPMENT_PLAN slices 2-3, the Codex
prompt's "Slice 2"). Pure computation; no external APIs, no spending.

New schemas (`schemas.py`): `ProductCandidate`, `NicheCandidate`,
`AssumptionRecord`, `Channel`, `ChannelRecommendation`, `CriterionScore`,
`ScoreResult`, `ScoreVerdict`, `AssumptionStatus`.

New module (`scoring.py`): `score_product`, `score_niche`, `classify_assumption`,
`recommend_channel`. Scoring weights/thresholds live in `rules.py`.

```text
[x] python -m pytest                       -> 23 passed
[x] python -m ruff check .                 -> All checks passed
[x] python -m marketmind.cli calc-sample   -> valid JSON
[x] python -m marketmind.cli score-sample  -> explainable score (pass, shopify storefront_first)
```

Behavior covered by tests: good/risky/rejected products; marketplace-first vs
storefront-first channel routing; strong/weak/unverified assumptions (an
unsourced claim can never be VERIFIED); regulated/blocked rejection. Confidence
is capped by evidence quality so unverified ideas never look certain.

Safety unchanged: still no external API calls, payments, publishing, credential
access, or messaging. All risky actions remain blocked pending future approval
gates.

## Known limitations

- No dashboard yet.
- No database yet.
- No approval queue implementation yet.
- No product finder implementation yet.
- No source adapters yet.
- No Stripe, Shopify, supplier, or ad platform integrations yet.
- No pp_brain domain pack yet.

## Safety status

The current code does not call external APIs, spend money, publish products, access credentials, or send messages.

## Next required verification

Run:

```bash
python -m pip install -e .[dev]
python -m pytest
python -m marketmind.cli
```

Then update this audit with actual results.
