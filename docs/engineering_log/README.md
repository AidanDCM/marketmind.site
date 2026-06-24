# Engineering Log — per-entry files (append-only)

Every significant change to MarketMind Autopilot gets its **own file** here.
`CHANGELOG.md` is the product-facing slice summary; this directory is the
**forensic ledger** for future developers and agents: why, where, when, what
 broke, and exactly what was run to verify.

## When to write an entry (binding)

Create a new file for **every**:

- Slice merge (Overview navigation, operator tooling, API behavior)
- Bug fix or incident repair
- Approval-gate, commerce integration, or experiment-rule change
- New audit triad (see `docs/audits/README.md`)
- Process or testing-discipline change
- Post-completion hardening pass (test added, flake fixed, rebuild)

**Do not** skip the log because the change "felt small." Minuscule details compound
into the only record that reconstructs a bad deploy or a silent approval bypass.

## Filename

`YYYY-MM-DD-<slug>.md` (UTC date). Multiple entries same day:

`YYYY-MM-DD-NN-<slug>.md` (e.g. `2026-06-24-02-overview-cac-link.md`).

Never edit or delete an existing entry. Corrections are **new** files that link
the entry they correct.

## Entry template

```markdown
# YYYY-MM-DD — short title

- **Author:** (human / AI agent + session id if known)
- **Commit(s)/PR:**
- **Where:** (paths, endpoints, UI surfaces)
- **When:** (UTC timestamp of change / merge)
- **What changed:** (exhaustive — behavior, not just file list)
- **Why (evidence):** (symptom, slice goal, incident, or operator request)
- **What could still break:**
- **Verification (commands + results):**
  - `python -m pytest -q tests/...` → N passed
  - `cd desktop && npm test` → …
  - (paste exit codes; never "tests passed" without evidence)
- **Follow-up:**
```

## Reading order

Sort filenames by date. Read `CHANGELOG.md` for the slice map; read here for
the full story behind each slice.
