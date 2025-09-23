# Phase 7 – Multi‑Brain Integration & Global Scaling

This document describes how to evolve MarketMind into a distributed, multi‑brain, globally scalable system while preserving auditability and safety.

## Goals
- Multi‑brain orchestration with a central coordinator
- Global scaling: markets, currencies, languages, taxes
- Autonomous decisions with complete audit trail
- Cross‑brain communication and learning
- Enterprise‑grade resilience and observability

## Architecture Overview
- Central Orchestrator (service) coordinates specialized brains (containers/services):
  - Pricing Brain
  - Marketing Brain
  - Analytics Brain
  - Compliance Brain
  - Expansion Brain
- Shared Infra:
  - API: `apps/hive_api/` (FastAPI)
  - Workers: `apps/hive_worker/` (Celery)
  - DB: PostgreSQL (production), SQLite (dev)
  - Cache/Bus: Redis (present) with optional Kafka for high‑throughput events
  - Dashboard: Next.js console (`apps/console/`)

Each brain exposes:
- Command interface (FastAPI or Celery task endpoints)
- Subscribes/Publishes to a shared bus (Redis streams or Kafka topics)
- Writes decisions, KPIs, and audits to SQL + Google Sheets

## Orchestration Contracts
- Task assignment: Orchestrator dispatches jobs to brains via Celery queues per brain (e.g., `queue=pricing`, `queue=marketing`).
- State & Idempotency: All brains upsert checkpoints using `IngestCheckpoint` (`packages/shared/models_db.py`) for replay safety.
- Message schema (event bus):
  - topic: `kpi.<brain>` — payload `{org_id, brain_id, metric, value, ts}`
  - topic: `decision.<brain>` — payload `{id, org_id, context, decision, reason, expected_roi, ts}`
  - topic: `insight.share` — payload `{source_brain, hypothesis, segment, effect_size, ts}`

## Global Scaling
- Multi‑market adapters: `packages/connectors/` adds per‑market modules (Amazon, eBay, Shopify, TikTok, Etsy). DRYRUN health already exists; production adapters should implement real API clients with retry & backoff.
- Currencies & FX: store currency per org/listing, add FX service (daily rates; mid‑market) and price normalization.
- Taxes: compliance brain evaluates VAT/GST/US sales tax rules per jurisdiction; pricing brain computes tax‑inclusive targets as needed.
- Logistics: per‑region shipping matrices; supplier selection by margin and SLA.
- Localization: copy translation and style variants per region; A/B testing hooks via marketing brain.

## Autonomy with Oversight
- Decision logging: all decisions persisted to SQL and mirrored to Google Sheets ledger (see CHANGELOG 2025‑08‑13).
- Audit trail: append‑only table with cryptographic hash chain (optional), plus Sheets for human review.
- Overrides: Admin dashboard controls to freeze a brain, override a decision, or adjust thresholds.

### Decision Ledger (Minimal)
- SQL models (SQLAlchemy 2.0) under `packages/database/models/decision.py`:
  - `DecisionLog(id, brain, decision_id, product_id, order_id, context JSON, decision JSON, reason, created_at)`
  - `KPIEvent(id, brain, metric, value, payload JSON, created_at)`
- Brain stubs append a `DecisionLog` row best‑effort (non‑fatal if DB unavailable) for auditability.

## Cross‑Brain Protocols
- Shared metrics bus: publish conversion rate, margin, CTR, CPC, CAC, ROAS.
- Feedback cycles: each brain runs retrospectives for 7/30/90 days and emits results; orchestrator schedules follow‑up experiments.
- Psychological learning pool: hypotheses (e.g., urgency copy) broadcast on `insight.share`; other brains auto‑schedule confirmatory tests within guardrails.

## Resilience & Scaling
- Failure isolation: if a brain is down, orchestrator reassigns tasks or queues work.
- Horizontal scaling: replicate brain containers; Celery autoscale and topic partitioning (Kafka optional) for throughput.
- Safety nets: fraud detection and compliance checks as separate brains in the pipeline.

## Implementation Notes (Repo Fit)
- Redis is already part of health checks; enable it for local orchestration (`make api-local-redis`).
- Start by defining Celery queues per brain and lightweight routers in API for orchestration endpoints.
- Keep DRYRUN switches for adapters; gate external side effects by environment flags.
- Extend `verify-integrations` to assert orchestrator + per‑brain health once brain services exist.
- Current script includes:
  - `GET /orchestrator/health`, `GET /orchestrator/queues`
  - Freeze/unfreeze round‑trip: `POST /orchestrator/freeze/{brain}?freeze=true|false`
  - Override acceptance: `POST /orchestrator/override?...`

## Rollout Plan
1) Define message contracts and Celery queues per brain.
2) Add minimal pricing/marketing/analytics brain skeletons (tasks + KPIs publish).
3) Implement orchestrator assignments and shared KPI ledger append.
4) Add localization and FX normalization layer.
5) Add compliance/tax rules and supplier selection heuristics.
6) Hardening: retries, timeouts, circuit breakers, rate‑limit backoff.
7) Load, chaos, and backtesting as per testing plan.
