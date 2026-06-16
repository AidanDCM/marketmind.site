# MarketMind Autopilot

MarketMind Autopilot is a human-in-the-loop commerce operator system. Its job is to research niches, find product opportunities, calculate unit economics, generate store and offer specs, prepare Codex build tasks, monitor P&L, and recommend safe actions for approval.

This repository is the public/startup-facing home for the MarketMind idea. It should stay clean, explainable, and safe enough to hand to Codex, future developers, or collaborators.

## Current purpose

The current site is a lightweight static landing page. The repo has now been upgraded with the planning documents needed to turn MarketMind from a landing page into a build-ready autonomous commerce operator.

## Product north star

> Build a safe commerce operating system where the bot does the work, Codex maintains the code, and Aidan stays the human approver for risky actions.

MarketMind should not be a random dropshipping bot. It should be a controlled system that can:

- research markets, products, suppliers, prices, and competitors
- score product opportunities with evidence and confidence
- calculate profit, break-even CAC, safe CAC, and kill/scale rules
- generate product, offer, landing-page, and store specs
- hand build tasks to Codex in small testable slices
- monitor ads, traffic, orders, refunds, support, and P&L
- prepare approval-gated actions instead of spending or publishing freely
- learn from results and improve future niche tests

## Human-in-the-loop rule

Aidan should not manually run the store. The bot should run the operating loop. Aidan's role is to:

- approve or deny high-risk actions
- check the dashboard and P&L
- review major strategy changes
- use Codex to maintain and improve the codebase
- shut down bad behavior quickly

## Safety stance

MarketMind must never silently:

- spend money above approved limits
- publish products without approval
- change prices live without approval
- order inventory without approval
- issue refunds without approval
- send external customer/supplier messages without approval
- access or expose secrets
- fake reviews, fake scarcity, fake identity, or misleading claims
- scrape protected, paywalled, CAPTCHA, or login-restricted systems

## Recommended build sequence

1. Commerce math engine
2. Product/item finder
3. Source/supplier adapters
4. Evidence and scoring engine
5. Landing page and offer spec generator
6. Read-only integrations
7. Approval dashboard
8. Approval-gated write actions
9. Daily autonomous operating loop
10. Multi-niche experiment runner

## Repository documents

- [`PROJECT_BRIEF.md`](PROJECT_BRIEF.md) — product summary, users, goals, scope, non-goals, assumptions
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — system design, modules, data flow, integration boundaries
- [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) — vertical slices and build order
- [`TEST_PLAN.md`](TEST_PLAN.md) — unit, integration, regression, safety, and manual tests
- [`APPROVAL_POLICY.md`](APPROVAL_POLICY.md) — what the bot can do automatically vs what needs approval
- [`PNL_MODEL.md`](PNL_MODEL.md) — unit economics, CAC, margin, kill/scale rules
- [`CODEX_HANDOFF.md`](CODEX_HANDOFF.md) — direct instructions for Codex or any developer
- [`docs/API_KEYS_AND_CREDENTIALS.md`](docs/API_KEYS_AND_CREDENTIALS.md) — sandbox-first, least-privilege credential setup (no real secrets)
- [`docs/decisions/0001-initial-architecture.md`](docs/decisions/0001-initial-architecture.md) — first architecture decision record
- [`docs/decisions/0002-parts-and-pieces-reuse.md`](docs/decisions/0002-parts-and-pieces-reuse.md) — Parts & Pieces reuse evaluation (which parts were adopted, deferred, or skipped)
- [`CHANGELOG.md`](CHANGELOG.md) — record of changes per slice
- [`.env.example`](.env.example) — safe environment variable template with no secrets

## Local preview

Open `index.html` in a browser.

## Deploy

This can be deployed through GitHub Pages, Netlify, Cloudflare Pages, or any static host.

## Status

Planning and public positioning are now upgraded. The next real engineering step is to build the commerce math engine as the first independently testable slice.
