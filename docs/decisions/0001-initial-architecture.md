# ADR-0001: Initial MarketMind Autopilot Architecture

## Status

Accepted

## Context

Aidan wants MarketMind to become a bot-run ecommerce/business operator where he is only the human in the loop. The bot should do the research, scoring, offer generation, monitoring, and daily store operations. Codex should maintain the code. Aidan should approve high-risk actions and watch the system through a dashboard.

The dangerous version would be a fully autonomous dropshipping bot that publishes products, spends money, changes prices, sends messages, and orders inventory without hard gates.

The safer version is a controlled commerce operator with strong unit economics, evidence verification, approval gates, logging, and testable slices.

## Decision

MarketMind will start as a local, testable commerce operating system rather than a live autonomous Shopify store.

The first architecture will use:

- static public landing page for positioning
- documentation-first project structure
- local Python commerce math engine as Slice 1
- SQLite and JSONL logs for V1 state/observability
- approval-first policy for all risky actions
- Stripe Payment Links or simple landing pages for earliest validation
- Shopify only after an offer proves demand
- future compatibility with Parts & Pieces, pp_brain, MCP tools, and Codex orchestration

The first code slice will be the commerce math engine, not a store integration.

## Consequences

### Better

- Safer starting point
- Lower chance of burning cash
- Clearer Codex handoff
- Easier testing
- Better alignment with Parts & Pieces philosophy
- Every later integration can depend on correct P&L math

### Worse

- Slower than launching a quick Shopify store
- No immediate live selling functionality in Slice 1
- Requires discipline to avoid overbuilding

### Future developers must remember

- Store integrations are not the foundation. Profit math and approval gates are the foundation.
- Live writes should come after dry-run and read-only modes.
- A missing or weak approval gate is a blocking defect.
- A product with bad economics should not be scaled just because it has clicks or revenue.
