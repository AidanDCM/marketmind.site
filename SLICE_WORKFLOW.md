# MarketMind Slice & Hardening Workflow

Binding instructions for Aidan and AI agents working on **MarketMind Autopilot**
(`marketmind.site`). Adapted from the Futures Trading Bot's testing discipline,
engineering log, and audit triad — **no trading concepts apply here**.

---

## Two phases

### Phase A — Slice building (current)

Each **`proceed`** from Aidan means **one testable slice**:

1. Pick the next operator/Overview gap (navigation, health panel, report line, API).
2. Implement the smallest correct diff.
3. **Microscope testing** (see below) — not only `pytest -q` green.
4. Update `CHANGELOG.md` + `OPERATING_INDEX.md` slice counter.
5. Add **`docs/engineering_log/YYYY-MM-DD-<slug>.md`** in the **same PR**.
6. Commit → push → PR → merge → sync `main` → delete feature branch.

### Phase B — System hardening (after slice roadmap complete)

When feature slices are done and Aidan still says **`proceed`**, each turn is **one**
of:

- **Test** — run deep system checks; add missing regression tests; record evidence.
- **Improve** — fix flakes, gaps, docs, or operator UX found in testing.
- **Rebuild** — repair broken subsystems with tests that encode the failure.

Never assume "done" without evidence in `reports/local_ci/TEST_LOG.md` and an
engineering-log entry.

---

## Microscope testing (every slice)

### Backend (required)

```powershell
python -m ruff check .
python -m pytest -q
python -m pytest -q tests/test_<area>.py   # focused module
```

708+ tests today (`tests/` mirrors `marketmind/`). Every behavior change adds a
regression test that names **what failure it prevents**.

### Desktop (required when touching `desktop/`)

```powershell
cd desktop
npm test
npm run build
```

28+ Vitest files today. Every new link/button/parser gets a component or unit test.

### Operator smoke (when touching API or deploy)

```powershell
python scripts/local_ci.py
# or full gate with API smoke:
python scripts/local_ci.py --full
```

### Evidence rule

Record exact commands and exit codes in:

- PR test plan
- `docs/engineering_log/` entry
- Append to `reports/local_ci/TEST_LOG.md` when running `local_ci`

**Never** claim green without pasted or logged results.

---

## Engineering log (non-negotiable)

See `docs/engineering_log/README.md`. One file per slice/change. Include:

- **Why** — operator pain, slice number, incident
- **Where** — UI route, API path, file
- **When** — UTC
- **Verification** — every command run

`CHANGELOG.md` is not a substitute.

---

## Audit triad (when adding analyses)

See `docs/audits/README.md`. Any recurring operator audit needs:

1. Tool — `scripts/<name>.py` + testable `marketmind/` module
2. Runbook — `docs/audits/<NAME>_RUNBOOK.md`
3. Report — committed under `reports/<name>/`

Existing partial triads: `verify_marketmind_deploy`, `check_operator_readiness`.

---

## MarketMind invariants (never weaken)

- Approval gate before live Stripe/Shopify writes (`dry_run=True` default).
- `logs/operator_events.jsonl` append-only.
- Experiment snapshots are P&L truth — no silent edits.
- Rule engine recommends only; execution requires approval where policy says so.

---

## Agent skills

| Skill | When |
|---|---|
| `.agents/skills/testing-marketmind-slice/SKILL.md` | Each feature slice |
| `.agents/skills/testing-marketmind-system/SKILL.md` | Phase B hardening |

---

## Related docs

- `AGENTS.md` — binding agent rules
- `docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md` — command reference
- `TEST_PLAN.md` — test categories and scenarios
- `OPERATING_INDEX.md` — doc map and slice counter
