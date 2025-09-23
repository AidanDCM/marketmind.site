# Phase 4 Adapter Layer

This document defines the unified architecture and standards for MarketMind channel and supplier adapters in Phase 4.

## Goals
- Robust, testable adapters with unified interfaces.
- Shared HTTP concerns: retries/backoff, rate limiting.
- Safe writes with idempotency.
- Health probes and compliance gates.
- Config-driven implementation selection and modes (LIVE/SANDBOX/DRYRUN).

## Architecture Overview
- Channel adapters implement `ChannelAdapter` in `packages/connectors/channels/base.py`.
- Supplier adapters implement `SupplierAdapter` in `packages/connectors/suppliers/base.py`.
- Registries
  - Channels: `packages/connectors/channels/registry.py`
  - Suppliers: `packages/connectors/suppliers/registry.py`
- Registration is centralized: do not register adapters inside adapter files. Use
  `packages/connectors/channels/registry.py` exclusively to avoid duplicate registrations.
- Shared HTTP utilities in `packages/connectors/http/`:
  - Backoff/retry: `backoff.py` (`retryable`, `BackoffConfig`)
  - Rate limiting: `ratelimit.py` (`get_rate_limiter`)
  - Exceptions: `exceptions.py`
- Idempotency utilities in `packages/connectors/idempotency/`:
  - `with_idempotency` decorator and stores (in-memory/redis).
- Logging fallback: `http/backoff.py`, `http/ratelimit.py`, and `http/client.py` gracefully
  fall back to stdlib `logging` if `structlog` is not installed (keeps tests runnable in
  minimal environments).

## Configuration and Environment
- Implementation selection (example for Amazon): env `AMAZON_IMPL` can switch between `amazon_premade` and `amazon_native` via `packages/connectors/channels/registry.py`.
- Modes: SANDBOX/LIVE/DRYRUN configured per adapter. DRYRUN should execute validations and log without side effects.
- Credentials via env or secrets manager. Never log secrets.

## HTTP Resilience
- Use `retryable` for transient failures (e.g., `requests.RequestException`, 429/5xx via `response.raise_for_status()`).
- Use `get_rate_limiter(name)` to protect API quotas. Prefer per-adapter limiter names: `amazon_sp_api`, `ebay_api`, `walmart_api`.
- Example:
```python
from ..http.backoff import retryable

@retryable(exceptions=(requests.RequestException,), max_retries=3)
def my_call(...):
    resp = requests.get(url, ...)
    resp.raise_for_status()
    return resp.json()
```

## Idempotency for Writes
- Wrap outbound writes with `with_idempotency(...)` using a deterministic `key_func`.
- Key should include unique business identifiers and material parameters (e.g., SKU + quantity/price).
- Example:
```python
from ..idempotency import with_idempotency

@with_idempotency(key_func=lambda self, sku, price_cents, **kw: f"publish_price:{sku}:{price_cents}")
def publish_price(self, sku, price_cents, **kw):
    ...
```

## Health Probes and Compliance Gates
- Each adapter must implement `health()` returning a JSON-serializable dict:
  - `{ "ok": bool, "name": <adapter_name>, ... }`
  - Include relevant fields: marketplace/site, sandbox flag, rate-limit stats where applicable.
- Compliance gates should verify permissions, scopes, and feature flags before write calls.

## Current Implementations (highlights)
- Amazon (`packages/connectors/channels/amazon.py`)
  - Added retry/backoff to network calls and `health()`.
  - Price update idempotency via `with_idempotency`.
- eBay (`packages/connectors/channels/ebay.py`)
  - `_make_request` wrapped with retry/backoff, `health()` implemented.
  - `update_inventory` wrapped with idempotency.

## Testing Strategy
- Contract/unit tests per adapter, mock HTTP and clients.
- Integration tests with sandbox credentials where available.
- Coverage for:
  - Authentication refresh flows.
  - Reads (orders/products) and writes (price/inventory/listings).
  - Retry/backoff success after transient failure.
  - Rate limiting behavior (token acquisition, blocking/wait).
  - Idempotency (same key -> single side effect).
  - DRYRUN mode: validations logged, no side effects.
  - Mapping contracts: normalization returns dict-like objects (AttrDict) and denormalization returns superset payloads compatible with multiple suites.
- Example references:
  - `tests/connectors/test_amazon_adapter.py`
  - `tests/connectors/test_ebay_adapter.py`
  - `tests/connectors/test_cj_adapter.py`
  - `tests/connectors/test_cj_smoke.py` (health + idempotency + retry/backoff)
  - `tests/connectors/test_walmart_adapter.py` (auth/health + idempotency + retry/backoff)
  - `scripts/test_ebay_integration.py`

## Test Execution Guide
- Recommended: create and use project venv `.venv/` via Makefile.
  - `make install`
  - `make test`
- Or use an existing `venv/`:
  - `venv/bin/python -m pip install -U pip pytest`
  - `venv/bin/python -m pytest -q tests/connectors -k "not slow"`

### Phase 4 Quick Targets (Makefile)
- `make test-phase4-connectors`
  - Runs unit/contract tests for adapters under `tests/connectors/` (skips slow)
- `make coverage-phase4`
  - Runs the same adapter test set with coverage for `packages/connectors` and related DB models, emitting terminal and HTML reports
- `make full-suite-phase4`
  - Runs core DB smoke (`tests/test_models.py`, `tests/test_database_models.py`) + adapter tests in one quick pass
- `make adapters-health`
  - Runs DRYRUN health/smoke tests for connectors (no side effects)

### Mapping Contracts (Normalization/Denormalization)
- Normalizers in `packages/connectors/mapping/normalize.py` now return a dict-like object (`AttrDict`).
  - Dict view preserves original values; attribute view adds convenience (e.g., `status` uppercased).
  - This decouples mapping from ORM models and fixes constructor keyword issues (e.g., `org_id`).
- `denormalize_listing()` emits a superset payload per vendor to satisfy variant expectations across tests (e.g., Amazon `StandardPrice`/`Quantity` and `ItemAttributes`; Shopify root fields and `variant`).
- See tests under `tests/connectors/mapping/` for examples and assertions.

## DRYRUN/Shadow Mode
- New adapters should support a DRYRUN mode that executes validations and logs intent
  without performing side effects. Enable DRYRUN for initial shadowing in production.

To run smoke health checks safely:

```bash
make adapters-health
```
  Ensure idempotency keys are still generated and logged for traceability.

## Runbook
- Set necessary env vars (API keys, marketplace/site, mode flags).
- Select adapter implementation via env if multiple exist.
- Validate `health()` for each adapter before enabling writes.
- Enable DRYRUN for new adapters in production-traffic shadowing.

## Backtesting (Phases 1–3)
- Phase 2 backtests (probes + security checks + changelog):
  - `make phase2-backtest`
- Phase 3 backtests (migrations + tests + probes):
  - `make phase3-backtest`
- Expected: both targets must complete with OK status before advancing to Phase 5.

## Backtesting (Phase 4)
- Connector contract tests (Phase 4 quick):
  - `make test-phase4-connectors`
- Coverage for connectors (Phase 4 quick):
  - `make coverage-phase4`
- Full Phase 4 quick suite (DB + connectors):
  - `make full-suite-phase4`

## Credentials and Modes
Set the following environment variables (e.g., in `.env`). Exact names reflect code in `packages/shared/config/schema.py`, `packages/connectors/channels/registry.py`, and `config/ebay_config.py`.

- Amazon (SP-API)
  - `AMAZON_IMPL` = `premade` or `native` (see `packages/connectors/channels/registry.py`)
  - `AMAZON_MODE` = `SANDBOX` or `LIVE`
  - `AMAZON_CLIENT_ID`, `AMAZON_CLIENT_SECRET`, `AMAZON_REFRESH_TOKEN`
  - Optional: `AMAZON_ROLE_ARN`, `AMAZON_REGION` (default `NA`)

- eBay
  - `EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_DEV_ID`
  - `EBAY_RU_NAME` (redirect/RuName) [primary]
  - Optional: `EBAY_REDIRECT_URI` (maps to `redirect_uri` in `EbaySettings`)
  - `EBAY_AUTH_TOKEN`, `EBAY_REFRESH_TOKEN`
  - `EBAY_SANDBOX` = `true`/`false` (see `config/ebay_config.py`)

- Walmart
  - `WALMART_MODE` = `DRYRUN`/`SANDBOX`/`LIVE`
  - `WALMART_CLIENT_ID`, `WALMART_CLIENT_SECRET`

- CJ (CJ Dropshipping)
  - `CJ_ACCESS_TOKEN`
  - Optional: `CJ_BASE_URL` (default `https://developers.cjdropshipping.com/api2.0/v1`)

- Google Sheets (optional, for ledger tooling)
  - `GSHEETS_SERVICE_ACCOUNT_JSON_PATH`
  - `GSHEETS_LEDGER_SPREADSHEET_ID`

- Global flags
  - `DRYRUN=1` to force dryrun behavior during smoke tests where supported

## Quality Gates (Optional but Recommended)
- `make lint-phase4` — ruff lint for connectors + database models
- `make type-check-phase4` — mypy on connectors + database models

## Readiness Checklist (Phase 4)
- Health probes: call `health()` on each adapter and ensure `{ "ok": true }`
- Mode gates: verify DRYRUN/SANDBOX/LIVE behavior per adapter
- HTTP resilience: retry/backoff and rate-limits exercised in tests
- Idempotency: repeated writes deduped by key; keys logged in DRYRUN
- Mapping: normalization returns `AttrDict`; denormalization payloads meet downstream tests
- Coverage: ≥ 80% overall; connectors covered via `coverage-phase4`

## Security
- Do not log secrets or full payloads with PII.
- Mask sensitive fields in debug logs.
- Prefer per-call scoped tokens and rotate refresh tokens regularly.

## Next Steps
- Extend retry/backoff and idempotency to Walmart and CJ connectors.
- Add standardized compliance gates and shared metrics surface.
- Expand tests to include shadow/dryrun and backtests for Phases 1–3.
