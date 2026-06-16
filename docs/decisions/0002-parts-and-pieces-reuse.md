# ADR-0002: Parts & Pieces Reuse Decisions

## Status
Accepted

## Context
MarketMind Autopilot is built under the Parts & Pieces Developer Operating System
(`AidanDCM/Parts-and-Pieces`). The OS requires that before building any new
module, the developer checks `PARTS_INDEX.md` and existing parts for reuse
candidates. This record documents which parts were evaluated, which were adopted,
which were intentionally not used, and which must be used in future slices.

## Reuse evaluation (as of Slice 4)

### Parts evaluated

| Part | Location | Status | Rationale |
|---|---|---|---|
| `ExplainableScorer` | `parts/python/explainable_scoring/` | **Adapted pattern, different interface** | Parts version uses integer weights (0-100 points) and a bool-check API. MarketMind scoring uses 0-1 float ratings, weighted averages, and multi-field input structs. The output shape is structurally the same (score + band/verdict + reasons + risks). We implement the same pattern independently behind the same interface rather than importing directly, because the data contract differs enough that forced reuse would add indirection without benefit. This decision must be revisited if a unified float-weight version is contributed back to Parts & Pieces. |
| `evidence_verifier.assess_evidence` | `parts/python/evidence_verifier/` | **Adapted pattern, simpler scope** | Parts version is field-level (required_fields, conflict flags, source URLs). MarketMind's `classify_assumption` is statement-level (a single evidence_quality float + source string). The core invariant is the same: unsourced claims cannot be marked verified. If assumption tracking grows to field-level granularity in a later slice, this part should be imported directly. |
| `DecisionGate` | `parts/python/decision_gate/` | **Deferred — use in Slice 6** | The approval engine (Slice 6) maps directly to this pattern: sequential rules, first-failure wins, approve if no rule fires. Slice 6 should import `DecisionGate` rather than building its own sequential rule runner. |
| `JsonlEventLedger` | `parts/python/event_ledger/` | **Deferred — use in Slice 7/8** | The daily report (Slice 8) and read-only import layer (Slice 7) both need append-only structured event logging. This part should be imported as-is rather than rebuilt. |
| `CsvSourceAdapter` | `parts/python/source_adapters/` | **Deferred — use in Slice 7** | Slice 7 imports CSV product/ad/order data. This part normalizes vendor-messy column names into internal records. Should be imported and wrapped with MarketMind-specific aliases (product_name, est_sale_price, etc.) rather than rebuilt. |
| `ChecklistGate` | `parts/python/checklist_gate/` | **Deferred — use in Slice 6** | The approval record schema in APPROVAL_POLICY.md maps directly to a checklist: each approval is a set of required fields (evidence, rollback, cost, confidence) that must be complete before execution. Slice 6 should adapt this. |
| `signal_engine` | `parts/python/signal_engine/` | **Not applicable** | The generic signal engine is designed for trading/recommender context-regime classification. MarketMind's scoring engine is simpler and commerce-specific. No reuse benefit. |
| `jsonl_telemetry` | `parts/python/jsonl_telemetry/` | **Same as JsonlEventLedger** | Overlaps with the event_ledger part above. Will evaluate which fits better at Slice 7/8. |
| `run_once_chain` | `parts/python/run_once_chain/` | **Deferred — possible Slice 5** | The spec generator (Slice 5) runs a fixed sequence of generation steps (headline → bundle → FAQ → CTA → analytics events). This part may be a good fit if the chain becomes conditional. Evaluate at Slice 5. |

## Consequences

### What gets better
- Future developers and AI agents can see immediately which Parts & Pieces parts
  are already evaluated and what to do with them.
- Slices 6, 7, 8 have a clear mandate to import proven parts rather than rebuild.

### What gets worse
- Two modules (`scoring.py`, `classify_assumption`) implement patterns that exist
  in Parts & Pieces without importing them. This is a deliberate decision, not an
  oversight, but it creates divergence that must be managed.

### What future developers must remember
- Slice 6 MUST use `DecisionGate` and `ChecklistGate` — do not build a custom
  sequential approval runner.
- Slice 7 MUST use `CsvSourceAdapter` — do not build a custom CSV normalizer.
- Slice 7/8 MUST use `JsonlEventLedger` — do not build a custom JSONL logger.
- Any scoring improvement that generalizes beyond MarketMind (e.g., float-weight
  ExplainableScorer) should be contributed back to Parts & Pieces per Gate 8.

## Required Parts & Pieces contributions at project close (Gate 8)

When MarketMind Autopilot reaches a stable milestone, these should be returned:

1. The commerce unit economics pattern (`math_engine.py`) — generic enough to
   reuse for any margin/CAC/profitability calculator.
2. The channel-ladder recommendation pattern (`scoring.py:recommend_channel`) —
   reusable for any multi-platform product routing decision.
3. The experiment kill/scale rule pattern (`experiment_rules.py`) — reusable for
   any hypothesis-test-with-budget system.
4. The approval queue schema from Slice 6 — reusable for any human-in-the-loop
   action approval system.
