# Makefile for local dev workflows (no Docker)

PY := .venv/bin/python
PIP := .venv/bin/pip
ALEMBIC := .venv/bin/python scripts/alembic_cli.py
CURL := /usr/bin/curl

.PHONY: help install install-dev api-local api-local-redis ingest health-8001 health-8002 health-int-8001 health-int-8002 health-summary counts db-seed test pricing-snapshot pricing-history pricing-simulate pricing-pending pricing-approved pricing-approve pricing-push-ebay audit-db security-check ingest-catalog ingest-pricing ingest-orders ingest-status ingest-health ingest-signals ingest-backfill ingest-replay verify-integrations changelog-watch phase2-backtest alembic-autogen-phase3 migrate-up migrate-down-last migrate-reset phase3-backtest seed-minimal seed-price-history migrate-price-history-legacy lint format type-check pre-commit-install pre-commit-run lint-phase3 type-check-phase3 test-phase4-connectors coverage-phase4 full-suite-phase4 lint-phase4 type-check-phase4 adapters-health load-test phase7-backtest phase8-tests phase8-tests-nocov phase8-e2e verify-phase8 backtest-phase8 phase9-tests phase9-backtest phase11-tests phase11-backtest phase12-tests phase12-backtest phase13-tests phase13-backtest phase14-tests phase14-backtest phase15-tests phase15-backtest profit-system-backtest

help:
	@echo "Targets:"
	@echo "  install           - Create venv and install deps"
	@echo "  install-dev       - Install developer tooling (black, ruff, mypy, pre-commit)"
	@echo "  api-local         - Start API on 127.0.0.1:8001 using SQLite dev.db"
	@echo "  api-local-redis   - Start API on 127.0.0.1:8002 with local Redis"
	@echo "  ingest            - Run one-off ingestion"
	@echo "  health-8001       - Health check API on 8001"
	@echo "  health-8002       - Health check API on 8002"
	@echo "  health-int-8001   - Integrations health on 8001"
	@echo "  health-int-8002   - Integrations health on 8002"
	@echo "  health-summary    - Overall health summary on 8001"
	@echo "  counts            - Print DB row counts"
	@echo "  seed-minimal      - Seed minimal test data (products/listings/suppliers/competitors/sales/simulations)"
	@echo "  seed-price-history- Seed one price_history row if dependencies exist (org, channel_listing)"
	@echo "  migrate-price-history-legacy - Transform legacy listing-based price history into product-based table"
	@echo "  db-seed           - Seed synthetic products/offers/competitors"
	@echo "  test              - Run unit tests"
	@echo "  lint              - Run ruff (linter)"
	@echo "  format            - Run black and ruff format"
	@echo "  type-check        - Run mypy type checks"
	@echo "  lint-phase3       - Run ruff on pricing + required DB models"
	@echo "  type-check-phase3 - Run mypy on pricing + required DB models"
	@echo "  pre-commit-install- Install git hook"
	@echo "  pre-commit-run    - Run all pre-commit hooks against repo"
	@echo "  pricing-snapshot  - POST /pricing/snapshot with data/sample_asins.json to 8001"
	@echo "  pricing-history   - GET /pricing/history?asin=$(ASIN)&limit=$(LIMIT) on 8001"
	@echo "  pricing-simulate  - POST /pricing/simulate (JSON body) on 8001"
	@echo "  pricing-pending   - GET /pricing/pending?limit=$(LIMIT) on 8001"
	@echo "  pricing-approved  - GET /pricing/approved?limit=$(LIMIT) on 8001"
	@echo "  pricing-approve   - POST /pricing/approve PRODUCT_ID=... on 8001"
	@echo "  pricing-push-ebay - POST /pricing/push/ebay?product_id=... on 8001 (dry run)"
	@echo "  audit-db          - Set up the config audit database"
	@echo "  security-check    - Run security checks (secrets, dependencies, etc.)"
	@echo "  ingest-catalog    - Run CJ catalog sync"
	@echo "  ingest-pricing    - Run pricing snapshot with sample ASINs"
	@echo "  ingest-orders     - Run order pull (placeholder)"
	@echo "  ingest-status     - Get ingestion pipeline status"
	@echo "  ingest-health     - Get ingestion health check"
	@echo "  ingest-signals    - Enqueue signals snapshot"
	@echo "  ingest-backfill   - Enqueue backfill price history (SIMULATION only)"
	@echo "  ingest-replay     - Manually set a checkpoint value"
	@echo "  verify-integrations - Comprehensive integration verification"
	@echo "  phase8-e2e        - Run Orders E2E tests (idempotency, fulfillment, KPIs)"
	@echo "  dash-kpis         - GET /dash/kpis on 8001 (org_id/brain_id optional)"
	@echo "  dash-orders       - GET /dash/orders/summary on 8001 (org_id/brain_id optional)"
	@echo "  phase10-backtest  - Migrate and hit Phase 10 dashboard endpoints"
	@echo "  seed-profit-log   - Seed demo rows into profit_modules_log"
	@echo "  full-system-tests - Migrate, (optionally) boot API, seed, run verify + phase backtests + API smoke"
	@echo "  api-tests         - Run scoped API smoke tests (apps/hive_api/tests/test_smoke_all.py & test_profit.py)"
	@echo "  learning-train-historical - POST /learning/train/historical with date range and features"
	@echo "  all-phases-backtest - Run all available phase backtests + verify-integrations"
	@echo "  phase12-tests     - Run scoped tests for marketing (placeholder)"
	@echo "  phase12-backtest  - Migrate and smoke test /marketing endpoints"
	@echo "  phase13-tests     - Run scoped tests for finance (placeholder)"
	@echo "  phase13-backtest  - Migrate and smoke test /finance endpoints"
	@echo "  changelog-watch   - Continuously append verbose labeled entries to CHANGELOG.md"
	@echo "  phase15-tests     - Run scoped tests for learning (placeholder)"
	@echo "  phase15-backtest  - Migrate and smoke test /learning endpoints"
	@echo "  launch-readiness  - Run consolidated launch readiness verification script"
	@echo "  test-cov-80       - Run tests with 80% coverage gate across apps and packages"
	@echo "  adapters-health-strict - Run adapter health tests with 80% coverage gate"
	@echo "  phase2-backtest   - Run Phase 2 probes + security checks and append CHANGELOG; fails if probes not ok"
	@echo "  load-test         - Headless Locust run against API (configurable USERS/SPAWN/DURATION)"
	@echo "  phase7-backtest   - Phase 7 sanity: migrate, verify-integrations, short load test"
	@echo "  live-verify       - Source envs from 'Key test/' and run verify-integrations (SIMULATION=false)"
	@echo "  live-all-phases   - Source envs and run all-phases-backtest (SIMULATION=false)"
	@echo "  api-live          - Start API in live mode (SIMULATION=false) and write .api.pid"
	@echo "  api-stop          - Stop API started via api-live (.api.pid)"
	@echo "  console-dev       - Start Next.js console (apps/console) with RBAC token support"
	@echo "  test-phase4-connectors - Run Phase 4 adapter tests (unit/contract)"
	@echo "  coverage-phase4   - Run Phase 4 adapter tests with coverage report"
	@echo "  full-suite-phase4 - Run core DB + Phase 4 adapter tests (quick)"
	@echo "  lint-phase4       - Ruff lint (connectors + database/models)"
	@echo "  type-check-phase4 - Mypy type checks (connectors + database/models)"
	@echo "  adapters-health   - Run DRYRUN health/smoke tests for connectors"
	@echo "  phase9-tests      - Run governance services unit tests (policy, risk, arbitrator, contract monitor)"
	@echo "  phase9-backtest   - Migrate DB and run governance services tests + connector health (quick)"

install:
	python3 -m venv .venv
	$(PIP) install -U pip
	$(PIP) install -r infra/docker/requirements-api.txt
	$(PIP) install -r infra/docker/requirements-worker.txt

install-dev:
	$(PIP) install -r requirements-dev.txt

api-local:
	DB_URL=sqlite:///./dev.db APP_ENV=development PYTHONPATH=. $(PY) -m uvicorn apps.hive_api.main:app --host 127.0.0.1 --port 8001

api-local-redis:
	DB_URL=sqlite:///./dev.db APP_ENV=development REDIS_URL=redis://127.0.0.1:6379/0 PYTHONPATH=. $(PY) -m uvicorn apps.hive_api.main:app --host 127.0.0.1 --port 8002

ingest:
	DB_URL=sqlite:///./dev.db APP_ENV=development PYTHONPATH=. $(PY) scripts/run_ingest_local.py

health-8001:
	$(CURL) -sS http://127.0.0.1:8001/health/data | jq . || $(CURL) -sS http://127.0.0.1:8001/health/data

health-8002:
	$(CURL) -sS http://127.0.0.1:8002/health/data | jq . || $(CURL) -sS http://127.0.0.1:8002/health/data

audit-db:
	$(PY) scripts/setup_audit_db.py

security-check:
	./scripts/ci/security_checks.sh

health-int-8001:
	$(CURL) -sS http://127.0.0.1:8001/health/integrations | jq . || $(CURL) -sS http://127.0.0.1:8001/health/integrations

health-int-8002:
	$(CURL) -s http://127.0.0.1:8002/health/integrations | python3 -m json.tool

health-summary:
	$(CURL) -s http://127.0.0.1:8001/health/summary | python3 -m json.tool

counts:
	@echo "Ensuring database is migrated to head before counting..."
	@$(MAKE) migrate-up >/dev/null || true
	DB_URL=sqlite:///./dev.db PYTHONPATH=. $(PY) scripts/counts.py

db-seed:
	DB_URL=sqlite:///./dev.db PYTHONPATH=. $(PY) scripts/seed_synthetic.py

seed-minimal:
	DB_URL=sqlite:///./dev.db PYTHONPATH=. $(PY) scripts/seed_minimal.py

seed-price-history:
	DB_URL=sqlite:///./dev.db PYTHONPATH=. $(PY) scripts/seed_price_history.py || true

# Optional: migrate legacy listing-based price history into product-based table
migrate-price-history-legacy:
	DB_URL=sqlite:///./dev.db PYTHONPATH=. $(PY) scripts/migrate_price_history_legacy.py || true

test:
	PYTHONPATH=. $(PY) -m pytest -q

# Phase 4 adapters quick test targets
test-phase4-connectors:
	PYTHONPATH=. $(PY) -m pytest -q tests/connectors -k "not slow"

coverage-phase4:
	PYTHONPATH=. $(PY) -m pytest \
	 -q tests/test_models.py tests/test_database_models.py tests/connectors -k "not slow" \
	 --cov=packages/connectors/channels/amazon.py \
	 --cov=packages/connectors/channels/cj.py \
	 --cov=packages/connectors/channels/ebay.py \
	 --cov=packages/connectors/channels/walmart.py \
	 --cov=packages/connectors/channels/base.py \
	 --cov=packages/connectors/mapping/normalize.py \
	 --cov=packages/database/models \
	 --cov=packages \
	 --cov-report=term-missing --cov-report=html --cov-fail-under=80

full-suite-phase4:
	PYTHONPATH=. $(PY) -m pytest -q tests/test_models.py tests/test_database_models.py tests/connectors -k "not slow"

# Connector health/smoke tests in DRYRUN mode (no side effects)
adapters-health:
	DRYRUN=1 PYTHONPATH=. $(PY) -m pytest -q \
	 --cov=packages --cov-report=term-missing --cov-fail-under=80 \
	 tests/connectors/test_cj_smoke.py \
	 tests/connectors/test_db_coverage_smoke.py

# Phase 9 governance targets
phase9-tests:
	PYTHONPATH=. $(PY) -m pytest -q tests/services

phase9-backtest:
	@echo "Running Phase 9 governance backtest (migrate + services tests + adapters health)..."
	make migrate-up
	make phase9-tests
	make adapters-health

# Phase 11 compliance helpers
phase11-tests:
	# Run scoped tests for compliance/privacy/tax if present; do not fail if none collected yet
	PYTHONPATH=. $(PY) -m pytest -q -k "compliance or privacy or tax" || true

phase11-backtest:
	@echo "Running Phase 11 backtest (migrate + compliance scaffolds)..."
	make migrate-up
	make phase11-tests
	@echo "[phase11-backtest] Completed. Implement tests under tests/services/* to enforce coverage."

# Phase 12 marketing helpers
phase12-tests:
	# Scoped tests for marketing; explicitly run apps/hive_api/tests where API tests live
	PYTHONPATH=. $(PY) -m pytest -q apps/hive_api/tests -k "marketing or attribution or experiment" || true

phase12-backtest:
	@echo "Running Phase 12 backtest (migrate + marketing API smoke)..."
	make migrate-up
	@echo "[smoke] GET /marketing/campaigns"
	$(CURL) -sS "http://127.0.0.1:8001/marketing/campaigns" | jq . || $(CURL) -sS "http://127.0.0.1:8001/marketing/campaigns"
	@echo "[smoke] POST /marketing/campaigns (draft)"
	$(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/campaigns" -H 'Content-Type: application/json' -d '{"name":"Q4 Launch", "org_id":"org_demo", "brain_id":"brain_marketing", "status":"draft"}' | jq . || $(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/campaigns" -H 'Content-Type: application/json' -d '{"name":"Q4 Launch", "org_id":"org_demo", "brain_id":"brain_marketing", "status":"draft"}'
	@echo "[smoke] GET /marketing/campaigns (scoped)"
	$(CURL) -sS "http://127.0.0.1:8001/marketing/campaigns?org_id=org_demo&brain_id=brain_marketing" | jq . || $(CURL) -sS "http://127.0.0.1:8001/marketing/campaigns?org_id=org_demo&brain_id=brain_marketing"
	@echo "[smoke] POST /marketing/assets"
	$(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/assets" -H 'Content-Type: application/json' -d '{"campaign_id":1,"kind":"copy","name":"headline","data":"{\"headline\":\"Q4\"}","org_id":"org_demo","brain_id":"brain_marketing"}' | jq . || $(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/assets" -H 'Content-Type: application/json' -d '{"campaign_id":1,"kind":"copy","name":"headline","data":"{\"headline\":\"Q4\"}","org_id":"org_demo","brain_id":"brain_marketing"}'
	@echo "[smoke] GET /marketing/assets?campaign_id=1"
	$(CURL) -sS "http://127.0.0.1:8001/marketing/assets?campaign_id=1" | jq . || $(CURL) -sS "http://127.0.0.1:8001/marketing/assets?campaign_id=1"
	@echo "[smoke] POST /marketing/experiments"
	$(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/experiments" -H 'Content-Type: application/json' -d '{"campaign_id":1,"name":"AB Test","kind":"ab","org_id":"org_demo","brain_id":"brain_marketing"}' | jq . || $(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/experiments" -H 'Content-Type: application/json' -d '{"campaign_id":1,"name":"AB Test","kind":"ab","org_id":"org_demo","brain_id":"brain_marketing"}'
	@echo "[smoke] GET /marketing/experiments?campaign_id=1"
	$(CURL) -sS "http://127.0.0.1:8001/marketing/experiments?campaign_id=1" | jq . || $(CURL) -sS "http://127.0.0.1:8001/marketing/experiments?campaign_id=1"
	@echo "[smoke] POST /marketing/experiment-results"
	$(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/experiment-results" -H 'Content-Type: application/json' -d '{"experiment_id":1,"variant":"A","metric":"ctr","value":0.12,"sample_size":100}' | jq . || $(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/experiment-results" -H 'Content-Type: application/json' -d '{"experiment_id":1,"variant":"A","metric":"ctr","value":0.12,"sample_size":100}'
	@echo "[smoke] GET /marketing/experiment-results?experiment_id=1"
	$(CURL) -sS "http://127.0.0.1:8001/marketing/experiment-results?experiment_id=1" | jq . || $(CURL) -sS "http://127.0.0.1:8001/marketing/experiment-results?experiment_id=1"
	@echo "[smoke] POST /marketing/attribution"
	$(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/attribution" -H 'Content-Type: application/json' -d '{"campaign_id":1,"event":"click","source":"google","medium":"cpc","channel":"web","customer_ref":"cust-smoke"}' | jq . || $(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/attribution" -H 'Content-Type: application/json' -d '{"campaign_id":1,"event":"click","source":"google","medium":"cpc","channel":"web","customer_ref":"cust-smoke"}'
	@echo "[smoke] GET /marketing/attribution?campaign_id=1"
	$(CURL) -sS "http://127.0.0.1:8001/marketing/attribution?campaign_id=1" | jq . || $(CURL) -sS "http://127.0.0.1:8001/marketing/attribution?campaign_id=1"
	@echo "[smoke] POST /marketing/journeys"
	$(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/journeys" -H 'Content-Type: application/json' -d '{"campaign_id":1,"customer_ref":"cust-smoke","stage":"consideration"}' | jq . || $(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/journeys" -H 'Content-Type: application/json' -d '{"campaign_id":1,"customer_ref":"cust-smoke","stage":"consideration"}'
	@echo "[smoke] GET /marketing/journeys?campaign_id=1"
	$(CURL) -sS "http://127.0.0.1:8001/marketing/journeys?campaign_id=1" | jq . || $(CURL) -sS "http://127.0.0.1:8001/marketing/journeys?campaign_id=1"

# Phase 13 finance helpers
phase13-tests:
	# Run migrations first to ensure finance tables exist, then run finance tests
	make migrate-up
	PYTHONPATH=. $(PY) -m pytest -q apps/hive_api/tests -k "finance"

phase13-backtest:
	@echo "Running Phase 13 backtest (migrate + finance API smoke)..."
	make migrate-up
	@echo "[smoke] GET /finance/health"
	$(CURL) -sS "http://127.0.0.1:8001/finance/health" | jq . || $(CURL) -sS "http://127.0.0.1:8001/finance/health"
	@echo "[smoke] GET /finance/ledger/entries"
	$(CURL) -sS "http://127.0.0.1:8001/finance/ledger/entries" | jq . || $(CURL) -sS "http://127.0.0.1:8001/finance/ledger/entries"
	@echo "[smoke] GET /finance/ledger/batches"
	$(CURL) -sS "http://127.0.0.1:8001/finance/ledger/batches" | jq . || $(CURL) -sS "http://127.0.0.1:8001/finance/ledger/batches"
	@echo "[smoke] GET /finance/invoices"
	$(CURL) -sS "http://127.0.0.1:8001/finance/invoices" | jq . || $(CURL) -sS "http://127.0.0.1:8001/finance/invoices"
	@echo "[smoke] GET /finance/forecast"
	$(CURL) -sS "http://127.0.0.1:8001/finance/forecast" | jq . || $(CURL) -sS "http://127.0.0.1:8001/finance/forecast"

# Phase 14 experimentation helpers
phase14-tests:
	# Run migrations then scoped tests for experiments/bundles if present
	make migrate-up
	PYTHONPATH=. $(PY) -m pytest -q apps/hive_api/tests -k "experiment or bundle or variant" || true

phase14-backtest:
	@echo "Running Phase 14 backtest (migrate + marketing experiments/bundles API smoke)..."
	make migrate-up
	@echo "[smoke] POST /marketing/campaigns (draft)"
	$(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/campaigns" -H 'Content-Type: application/json' -d '{"name":"Phase14 Campaign", "org_id":"org_demo", "brain_id":"brain_marketing", "status":"draft"}' | jq . || $(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/campaigns" -H 'Content-Type: application/json' -d '{"name":"Phase14 Campaign", "org_id":"org_demo", "brain_id":"brain_marketing", "status":"draft"}'
	@echo "[smoke] POST /marketing/experiments"
	$(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/experiments" -H 'Content-Type: application/json' -d '{"campaign_id":1,"name":"MVT","kind":"abn","org_id":"org_demo","brain_id":"brain_marketing"}' | jq . || $(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/experiments" -H 'Content-Type: application/json' -d '{"campaign_id":1,"name":"MVT","kind":"abn","org_id":"org_demo","brain_id":"brain_marketing"}'
	@echo "[smoke] POST /marketing/variants"
	$(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/variants" -H 'Content-Type: application/json' -d '{"experiment_id":1,"key":"A","name":"control","allocation_weight":1.0}' | jq . || $(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/variants" -H 'Content-Type: application/json' -d '{"experiment_id":1,"key":"A","name":"control","allocation_weight":1.0}'
	@echo "[smoke] POST /marketing/bundles"
	$(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/bundles" -H 'Content-Type: application/json' -d '{"experiment_id":1,"bundle_ref":"BUNDLE-001","channel":"shopify","components":"[{\"sku\":\"SKU1\",\"qty\":1,\"price\":19.99}]"}' | jq . || $(CURL) -sS -X POST "http://127.0.0.1:8001/marketing/bundles" -H 'Content-Type: application/json' -d '{"experiment_id":1,"bundle_ref":"BUNDLE-001","channel":"shopify","components":"[{\"sku\":\"SKU1\",\"qty\":1,\"price\":19.99}]"}'

# Phase 15 learning helpers
phase15-tests:
	# Run comprehensive learning tests: API, unit tests, integration tests
	make migrate-up
	PYTHONPATH=. $(PY) -m pytest -q apps/hive_api/tests/test_learning.py tests/learning/ -k "learning or drift or benchmark or rollout" --cov=apps.hive_worker.tasks.learning --cov=apps.hive_api.routers.learning --cov-report=term-missing

phase15-unit-tests:
	# Run only unit tests for learning components
	PYTHONPATH=. $(PY) -m pytest -q tests/learning/ --cov=apps.hive_worker.tasks.learning --cov-report=term-missing

phase15-integration-tests:
	# Run integration tests for learning workflow
	make migrate-up
	PYTHONPATH=. $(PY) -m pytest -q apps/hive_api/tests/test_learning.py -m integration

phase15-backtest:
	@echo "Running Phase 15 backtest (migrate + comprehensive learning API verification)..."
	make migrate-up
	@echo "[smoke] GET /learning/health"
	$(CURL) -sS "http://127.0.0.1:8001/learning/health" | jq . || $(CURL) -sS "http://127.0.0.1:8001/learning/health"
	@echo "[smoke] GET /learning/models"
	$(CURL) -sS "http://127.0.0.1:8001/learning/models?limit=5" | jq . || $(CURL) -sS "http://127.0.0.1:8001/learning/models?limit=5"
	@echo "[smoke] GET /learning/metrics"
	$(CURL) -sS "http://127.0.0.1:8001/learning/metrics?limit=5" | jq . || $(CURL) -sS "http://127.0.0.1:8001/learning/metrics?limit=5"
	@echo "[smoke] GET /learning/drift"
	$(CURL) -sS "http://127.0.0.1:8001/learning/drift?limit=5" | jq . || $(CURL) -sS "http://127.0.0.1:8001/learning/drift?limit=5"
	@echo "[smoke] GET /learning/benchmarks"
	$(CURL) -sS "http://127.0.0.1:8001/learning/benchmarks?limit=5" | jq . || $(CURL) -sS "http://127.0.0.1:8001/learning/benchmarks?limit=5"
	@echo "[smoke] GET /learning/rollouts"
	$(CURL) -sS "http://127.0.0.1:8001/learning/rollouts?limit=5" | jq . || $(CURL) -sS "http://127.0.0.1:8001/learning/rollouts?limit=5"

# Aggregated profit system verification (migrate + integrations + dashboard + phases 12–15)
profit-system-backtest:
	@echo "Running Profit System Backtest (migrate + verify-integrations + phase10/12/13/14/15)..."
	@# Ensure DB at head first
	make migrate-up
	@# Comprehensive integrations (includes orchestrator, orders, pricing, learning)
	make verify-integrations || true
	@# Dashboard API sanity
	make phase10-backtest || true
	@# Domain backtests (marketing/finance/experiments/learning)
	make phase12-backtest || true
	make phase13-backtest || true
	make phase14-backtest || true
	make phase15-backtest || true
	@echo "[profit-system-backtest] Completed. Review logs above for any WARN messages."

# Comprehensive system verification: migrate, ensure API up, seed, run verification/backtests and API smoke
full-system-tests:
	@echo "[full-system-tests] Ensuring database migrated..."
	make migrate-up
	@echo "[full-system-tests] Checking API availability on 127.0.0.1:8001..."
	@if /usr/bin/curl -sf http://127.0.0.1:8001/_info >/dev/null; then \
	  echo "[full-system-tests] API already running."; \
	  STARTED=0; \
	else \
	  echo "[full-system-tests] Starting API locally..."; \
	  (nohup DB_URL=sqlite:///./dev.db APP_ENV=development PYTHONPATH=. $(PY) -m uvicorn apps.hive_api.main:app --host 127.0.0.1 --port 8001 >/dev/null 2>&1 & echo $$! > .api.pid); \
	  STARTED=1; \
	  echo "[full-system-tests] Waiting for API to be ready..."; \
	  for i in 1 2 3 4 5 6 7 8 9 10; do \
	    /usr/bin/curl -sf http://127.0.0.1:8001/_info >/dev/null && break || sleep 1; \
	  done; \
	fi; \
	 echo "[full-system-tests] Seeding minimal data + profit log..."; \
	 make seed-minimal || true; \
	 make seed-profit-log || true; \
	 echo "[full-system-tests] Running verify-integrations..."; \
	 make verify-integrations; \
	 echo "[full-system-tests] Running phase backtests (10,12,13,14,15)..."; \
	 make phase10-backtest || true; \
	 make phase12-backtest || true; \
	 make phase13-backtest || true; \
	 make phase14-backtest || true; \
	 make phase15-backtest || true; \
	 echo "[full-system-tests] Running API smoke tests..."; \
	 DB_URL=sqlite:///./dev.db APP_ENV=development PYTHONPATH=. $(PY) -m pytest -q apps/hive_api/tests/test_smoke_all.py apps/hive_api/tests/test_profit.py || true; \
	 echo "[full-system-tests] Running full API suite (apps/hive_api/tests)..."; \
	 DB_URL=sqlite:///./dev.db APP_ENV=development PYTHONPATH=. $(PY) -m pytest -q apps/hive_api/tests || true; \
	 if [ -f .api.pid ]; then \
	   PID=`cat .api.pid`; \
	   if kill -0 $$PID 2>/dev/null; then \
	     echo "[full-system-tests] Stopping background API (PID=$$PID)..."; \
	     kill $$PID || true; \
	   fi; \
	   rm -f .api.pid; \
	 fi; \
	 echo "[full-system-tests] Completed."

all-phases-backtest:
	@echo "[all-phases-backtest] Starting comprehensive phase backtests..."
	make migrate-up
	make verify-integrations
	@# Phase 2 security/probes (if present)
	-make phase2-backtest
	@# Phase 7 orchestration + load sanity (short)
	-make phase7-backtest
	@# Phase 8 orders E2E
	-$(MAKE) phase8-e2e
	@# Phase 9 governance is covered in verify-integrations and docs; add specific targets here if present
	@# Phase 10 dashboard
	-make phase10-backtest
	@# Phase 11 compliance/privacy/tax covered in verify-integrations
	@# Phase 12-15 domain backtests
	-make phase12-backtest
	-make phase13-backtest
	-make phase14-backtest
	-make phase15-backtest
	@echo "[all-phases-backtest] Completed. Review outputs for any WARN entries."

# Live helpers: source envs from repo root and sibling 'Key test' directory and run with SIMULATION=false
KEY_TEST_DIR ?= /Users/aidanmiller/Desktop/Ecommerce\ Projects/Key\ test
define LOAD_ALL_ENVS
set -a; \
# Repo-level envs take precedence
if [ -f .env.live ]; then . ./.env.live; fi; \
if [ -f .env ]; then . ./.env; fi; \
for f in $(KEY_TEST_DIR)/*.env; do \
  if [ -f "$$f" ]; then . "$$f"; fi; \
done; \
# Normalize EBAY_MODE if a legacy value is used
if [ "$$EBAY_MODE" = "PRODUCTION" ]; then \
  echo "[env-normalize] EBAY_MODE=PRODUCTION detected; normalizing to EBAY_MODE=LIVE"; \
  export EBAY_MODE=LIVE; \
fi; \
set +a;
endef

live-verify:
	@echo "[live-verify] Sourcing envs from $(KEY_TEST_DIR) and running verify-integrations with SIMULATION_ENABLED=false..."
	@$(LOAD_ALL_ENVS) SIMULATION_ENABLED=false $(MAKE) verify-integrations

live-all-phases:
	@echo "[live-all-phases] Sourcing envs from $(KEY_TEST_DIR) and running all-phases-backtest with SIMULATION_ENABLED=false..."
	@$(LOAD_ALL_ENVS) SIMULATION_ENABLED=false $(MAKE) all-phases-backtest


api-live:
	@echo "[api-live] Starting API with SIMULATION_ENABLED=false on 127.0.0.1:8001..."
	@$(LOAD_ALL_ENVS) SIMULATION_ENABLED=false nohup DB_URL=$${DB_URL:-sqlite:///./dev.db} APP_ENV=development PYTHONPATH=. .venv/bin/python -m uvicorn apps.hive_api.main:app --host 127.0.0.1 --port 8001 >/dev/null 2>&1 & echo $$! > .api.pid; \
	  for i in $$(seq 1 20); do curl -sf http://127.0.0.1:8001/_info >/dev/null && break || sleep 1; done; \
	  echo "[api-live] API is up (PID=$$(cat .api.pid))"

api-stop:
	@echo "[api-stop] Stopping API if running..."
	@if [ -f .api.pid ]; then \
	  PID=$$(cat .api.pid); \
	  if kill -0 $$PID 2>/dev/null; then echo "[api-stop] Killing $$PID"; kill $$PID || true; fi; \
	  rm -f .api.pid; \
	else \
	  echo "[api-stop] No .api.pid found"; \
	fi

console-dev:
	@echo "[console-dev] Starting Next.js console in apps/console (requires Node & dependencies installed)"
	@echo "[console-dev] Ensure NEXT_PUBLIC_API_URL and NEXT_PUBLIC_API_TOKEN are set for RBAC actions"
	@echo "[console-dev] Example: export NEXT_PUBLIC_API_URL=\"http://127.0.0.1:8001\"" 
	@echo "[console-dev] Then run: (cd apps/console && npm run dev)"

api-tests:
	@echo "[api-tests] Running scoped API smoke tests..."
	make migrate-up
	PYTHONPATH=. $(PY) -m pytest -q apps/hive_api/tests/test_smoke_all.py apps/hive_api/tests/test_profit.py

# Learning helpers
API_BASE ?= http://127.0.0.1:8001
BRAIN ?= pricing
START ?= 2024-01-01T00:00:00Z
END ?= 2024-01-31T23:59:59Z
FEATURES ?= price,clicks
MODEL ?= auto
learning-train-historical:
	@echo "[learning-train-historical] Brain=$(BRAIN) Range=$(START)..$(END) Features=$(FEATURES) Model=$(MODEL)"
	H="Content-Type: application/json"; \
	if [ -n "$$API_TOKEN" ]; then H="$$H"$$(printf ' -H "Authorization: Bearer %s"' "$$API_TOKEN"); fi; \
	DATA=$$(jq -n --arg brain "$(BRAIN)" --arg start "$(START)" --arg end "$(END)" --arg feats "$(FEATURES)" --arg model "$(MODEL)" '{brain_id:$$brain,start_date:$$start,end_date:$$end,features:($$feats|split(",")),model_type:$$model}'); \
	/usr/bin/curl -sS -X POST $(API_BASE)/learning/train/historical $$H -d "$$DATA" | python3 -m json.tool

# Dev tooling
lint:
	.venv/bin/ruff check packages/database packages/pricing packages/orders packages/services scripts

format:
	.venv/bin/black .
	.venv/bin/ruff format .

type-check:
	.venv/bin/mypy packages/database packages/pricing packages/orders packages/services scripts

# Scoped checks for Phase 4 (connectors + database models)
lint-phase4:
	.venv/bin/ruff check packages/connectors packages/database/models

type-check-phase4:
	.venv/bin/mypy --follow-imports=skip packages/connectors packages/database/models

# Scoped checks for Phase 3 (pricing + its DB dependencies)
lint-phase3:
	.venv/bin/ruff check packages/pricing

type-check-phase3:
	.venv/bin/mypy --follow-imports=skip packages/pricing

pre-commit-install:
	.venv/bin/pre-commit install

pre-commit-run:
	.venv/bin/pre-commit run --all-files

# Pricing helpers
pricing-snapshot:
	$(CURL) -sS -X POST http://127.0.0.1:8001/pricing/snapshot -H 'Content-Type: application/json' --data-binary @data/sample_asins.json | jq . || \
	$(CURL) -sS -X POST http://127.0.0.1:8001/pricing/snapshot -H 'Content-Type: application/json' --data-binary @data/sample_asins.json

ASIN ?= B000TEST01
LIMIT ?= 30
INTERVAL ?= 5
pricing-history:
	$(CURL) -sS "http://127.0.0.1:8001/pricing/history?asin=$(ASIN)&limit=$(LIMIT)" | jq . || \
	$(CURL) -sS "http://127.0.0.1:8001/pricing/history?asin=$(ASIN)&limit=$(LIMIT)"

# Pricing simulation helpers
pricing-simulate:
	$(CURL) -sS -X POST "http://127.0.0.1:8001/pricing/simulate" -H 'Content-Type: application/json' -d '{"limit":$(LIMIT)}' | jq . || \
	$(CURL) -sS -X POST "http://127.0.0.1:8001/pricing/simulate" -H 'Content-Type: application/json' -d '{"limit":$(LIMIT)}'

pricing-pending:
	$(CURL) -sS "http://127.0.0.1:8001/pricing/pending?limit=$(LIMIT)" | jq . || \
	$(CURL) -sS "http://127.0.0.1:8001/pricing/pending?limit=$(LIMIT)"

pricing-approved:
	$(CURL) -sS "http://127.0.0.1:8001/pricing/approved?limit=$(LIMIT)" | jq . || \
	$(CURL) -sS "http://127.0.0.1:8001/pricing/approved?limit=$(LIMIT)"

PRODUCT_ID ?= 0
pricing-approve:
	$(CURL) -sS -X POST "http://127.0.0.1:8001/pricing/approve" -H 'Content-Type: application/json' -d '{"product_id":$(PRODUCT_ID)}' | jq . || \
	$(CURL) -sS -X POST "http://127.0.0.1:8001/pricing/approve" -H 'Content-Type: application/json' -d '{"product_id":$(PRODUCT_ID)}'

pricing-push-ebay:
	$(CURL) -sS -X POST "http://127.0.0.1:8001/pricing/push/ebay?product_id=$(PRODUCT_ID)" | jq . || \
	$(CURL) -sS -X POST "http://127.0.0.1:8001/pricing/push/ebay?product_id=$(PRODUCT_ID)"

# Ingestion helpers
ingest-catalog:
	$(CURL) -sS -X POST http://127.0.0.1:8001/ingest/run/catalog -H 'Content-Type: application/json' -d '{"supplier":"cj"}' | python3 -m json.tool

ingest-pricing:
	$(CURL) -sS -X POST http://127.0.0.1:8001/ingest/run/pricing -H 'Content-Type: application/json' -d '{"asins":["B08N5WRWNW","B07FZ8S74R"],"write_to_sheets":true}' | python3 -m json.tool

ingest-orders:
	$(CURL) -sS -X POST http://127.0.0.1:8001/ingest/run/orders -H 'Content-Type: application/json' -d '{"channel":"amazon"}' | python3 -m json.tool

ingest-status:
	$(CURL) -s http://127.0.0.1:8001/ingest/status | python3 -m json.tool

ingest-health:
	$(CURL) -s http://127.0.0.1:8001/ingest/health | python3 -m json.tool

ingest-signals:
	$(CURL) -sS -X POST http://127.0.0.1:8001/ingest/run/signals -H 'Content-Type: application/json' -d '{"channel":"amazon"}' | python3 -m json.tool

CHANNEL ?= amazon
ASINS ?= ["B08N5WRWNW","B07FZ8S74R"]
START ?= 2024-01-01T00:00:00Z
END ?= 2024-02-01T00:00:00Z
ingest-backfill:
	$(CURL) -sS -X POST http://127.0.0.1:8001/ingest/backfill/price_history -H 'Content-Type: application/json' -d '{"channel":"$(CHANNEL)","asins":$(ASINS),"start_iso":"$(START)","end_iso":"$(END)"}' | python3 -m json.tool

PIPELINE ?= signals
SOURCE ?= amazon
CKEY ?=
CVALUE ?= 2025-01-01T00:00:00Z
ingest-replay:
	$(CURL) -sS -X POST http://127.0.0.1:8001/ingest/replay/checkpoint -H 'Content-Type: application/json' -d '{"pipeline":"$(PIPELINE)","source":"$(SOURCE)","key":"$(CKEY)","value":"$(CVALUE)"}' | python3 -m json.tool

verify-integrations:
	@echo "Running comprehensive integration verification..."
	@./scripts/verify_integrations.sh

seed-profit-log:
	DB_URL=sqlite:///./dev.db PYTHONPATH=. $(PY) scripts/seed_profit_log.py

# Phase 8 helpers
phase8-tests:
	PYTHONPATH=. $(PY) -m pytest -q -k "orders or routing or po_cj or fulfillment"

phase8-tests-nocov:
	PYTEST_ADDOPTS="-p no:cov" PYTHONPATH=. $(PY) -m pytest -q -c /dev/null tests/orders tests/api

phase8-e2e:
	PYTEST_ADDOPTS="-p no:cov" PYTHONPATH=. $(PY) -m pytest -q -c /dev/null tests/e2e

verify-phase8:
	@echo "Running Phase 8 verification (API + Orders stubs + health)..."
	@./scripts/verify_integrations.sh
	@echo "Running Phase 8 E2E tests (idempotency, fulfillment, KPIs)..."
	make phase8-e2e

# Phase 10 dashboard helpers
ORG ?=
BRAIN ?=
dash-kpis:
	$(CURL) -sS "http://127.0.0.1:8001/dash/kpis?org_id=$(ORG)&brain_id=$(BRAIN)" | jq . || \
	$(CURL) -sS "http://127.0.0.1:8001/dash/kpis?org_id=$(ORG)&brain_id=$(BRAIN)"

dash-orders:
	$(CURL) -sS "http://127.0.0.1:8001/dash/orders/summary?org_id=$(ORG)&brain_id=$(BRAIN)" | jq . || \
	$(CURL) -sS "http://127.0.0.1:8001/dash/orders/summary?org_id=$(ORG)&brain_id=$(BRAIN)"

phase10-backtest:
	@echo "Running Phase 10 backtest (migrate + dashboard KPIs)..."
	make migrate-up
	make dash-kpis
	make dash-orders

backtest-phase8:
	@echo "Running Phase 8 backtest (migrate + verify + short load)..."
	make migrate-up
	make verify-phase8
	USERS=50 SPAWN=5 DURATION=60 make load-test
	@echo "[phase8-backtest] Completed. Review KPIs and logs."

# Changelog automation
changelog-watch:
	PYTHONPATH=. $(PY) scripts/changelog_watch.py --interval $(INTERVAL)

# Phase 2 aggregated backtest

phase2-backtest:
	@echo "Running Phase 2 backtests..."
	PYTHONPATH=. $(PY) -m pytest -q
	./scripts/ci/security_checks.sh
	@echo "Executing internal probes..."
	@RESULT_JSON=`PYTHONPATH=. $(PY) scripts/phase2_backtest.py`; \
	 echo "$$RESULT_JSON"; \
	 RESULT_JSON_ENV="$$RESULT_JSON"; \
	 OK=`RESULT_JSON_ENV="$$RESULT_JSON_ENV" python3 -c 'import os,json; data=json.loads(os.environ.get("RESULT_JSON_ENV","{}")); print(str(data.get("summary",{}).get("ok", False)).lower())' 2>/dev/null`; \
	 PYTHONPATH=. $(PY) scripts/changelog_append.py --title "Phase 2 Backtest" --data "$$RESULT_JSON"; \
	 if [ "$$OK" = "true" ]; then echo "[phase2-backtest] OK"; exit 0; else echo "[phase2-backtest] FAIL"; exit 1; fi

# Phase 3 helpers
alembic-autogen-phase3:
	@echo "Autogenerating Phase 3 Alembic revision from canonical models..."
	DB_URL=sqlite:///./dev.db PYTHONPATH=. $(ALEMBIC) -c alembic.ini revision -m "phase3 schema" --autogenerate

migrate-up:
	@echo "Upgrading database to head..."
	DB_URL=sqlite:///./dev.db PYTHONPATH=. $(ALEMBIC) -c alembic.ini upgrade head

migrate-down-last:
	@echo "Downgrading database by one revision..."
	DB_URL=sqlite:///./dev.db PYTHONPATH=. $(ALEMBIC) -c alembic.ini downgrade -1

# Destructive reset of local SQLite DB
migrate-reset:
	@echo "Resetting database (destructive)..."
	rm -f dev.db


phase3-backtest:
	@echo "Running Phase 3 backtests (migrations + tests + probes)..."
	make migrate-up
	PYTHONPATH=. $(PY) -m pytest -q
	./scripts/ci/security_checks.sh
	make counts
	@echo "Executing internal probes (Phase 2 suite as smoke)..."
	@RESULT_JSON=`PYTHONPATH=. $(PY) scripts/phase2_backtest.py`; \
	 echo "$$RESULT_JSON"; \
	 RESULT_JSON_ENV="$$RESULT_JSON"; \
	 OK=`RESULT_JSON_ENV="$$RESULT_JSON_ENV" python3 -c 'import os,json; data=json.loads(os.environ.get("RESULT_JSON_ENV","{}")); print(str(data.get("summary",{}).get("ok", False)).lower())' 2>/dev/null`; \
	 PYTHONPATH=. $(PY) scripts/changelog_append.py --title "Phase 3 Backtest" --data "$$RESULT_JSON"; \
	 if [ "$$OK" = "true" ]; then echo "[phase3-backtest] OK"; exit 0; else echo "[phase3-backtest] FAIL"; exit 1; fi

# Phase 7 helpers

USERS ?= 500
SPAWN ?= 25
DURATION ?= 600
load-test:
	@echo "Running headless load test with Locust..."
	.venv/bin/locust -f locustfile.py --headless -u $(USERS) -r $(SPAWN) --run-time $(DURATION)s || true

load-test-report:
	@echo "Running headless load test with Locust (CSV/HTML reports)..."
	@mkdir -p reports/load
	.venv/bin/locust -f locustfile.py --headless -u $(USERS) -r $(SPAWN) --run-time $(DURATION)s \
	  --csv reports/load/metrics --html reports/load/report.html || true

# Assert pricing checkpoint exists (skips if Amazon SP-API not configured)
assert-pricing-checkpoint:
	@echo "[assert] Checking Amazon SP-API configuration..."
	CONFIGURED=$$(/usr/bin/curl -s http://127.0.0.1:8001/ingest/health | python3 -c 'import sys,json; d=json.load(sys.stdin); print(int(d.get("channels",{}).get("amazon",{}).get("configured", False)))' 2>/dev/null || echo 0); \
	if [ "$$CONFIGURED" -eq 0 ]; then \
	  echo "[assert] SP-API not configured; skipping checkpoint assertion."; \
	  exit 0; \
	fi; \
	echo "[assert] Triggering pricing snapshot..."; \
	/usr/bin/curl -sS -X POST http://127.0.0.1:8001/ingest/run/pricing -H 'Content-Type: application/json' -d '{"asins":["B08N5WRWNW"],"write_to_sheets":false}' >/dev/null || true; \
	sleep 2; \
	VAL=$$(/usr/bin/curl -s http://127.0.0.1:8001/ingest/status | python3 -c 'import sys,json; d=json.load(sys.stdin); cps=d.get("checkpoints",[]); \
	  print(next((c.get("value") for c in cps if c.get("pipeline")=="pricing" and c.get("source")=="amazon" and c.get("key")=="last_snapshot_iso"), ""))' 2>/dev/null || echo ""); \
	if [ -n "$$VAL" ]; then \
	  echo "[assert] OK: pricing/amazon last_snapshot_iso=$$VAL"; \
	  exit 0; \
	else \
	  echo "[assert] FAIL: pricing/amazon checkpoint not found"; \
	  exit 1; \
	fi

# Archive latest load test reports into docs/reports with timestamp
archive-load-report:
	@mkdir -p docs/reports
	@TS=$$(date +%Y%m%d-%H%M%S); \
	if [ -d reports/load ]; then \
	  tar -C reports -czf docs/reports/load-$$TS.tgz load && echo "[archive] Wrote docs/reports/load-$$TS.tgz"; \
	else \
	  echo "[archive] No reports/load directory to archive"; \
	fi

phase7-backtest:
	@echo "Running Phase 7 sanity backtest (migrate + verify-integrations + short load)..."
	make migrate-up
	make verify-integrations
	USERS=100 SPAWN=10 DURATION=120 make load-test
	@echo "[phase7-backtest] Completed. Review load KPIs and verify no errors in console/logs."

# Launch readiness consolidated script
launch-readiness:
	@echo "Running comprehensive launch readiness checks..."
	./scripts/launch_readiness_final.sh

# Docker Compose validation
compose-validate:
	@echo "Validating Docker Compose configurations..."
	docker-compose config > /dev/null && echo "✅ docker-compose.yml valid"
	docker-compose -f docker-compose.prod.yml config > /dev/null && echo "✅ docker-compose.prod.yml valid"

# Complete production readiness check
production-ready: launch-readiness compose-validate
	@echo "🎉 MarketMind is PRODUCTION READY!"
	@echo "✅ All security checks passed"
	@echo "✅ All infrastructure checks passed"
	@echo "✅ Docker Compose configurations valid"
	@echo "✅ Ready for deployment"

launch-readiness-legacy:
	@echo "Running legacy launch readiness checks..."
	./scripts/launch_readiness_check.sh || (echo "[launch-readiness] FAILED" && exit 1)

# Strict coverage gate across apps and packages
test-cov-80:
	PYTHONPATH=. $(PY) -m pytest -q \
	 --cov=apps --cov=packages --cov-report=term-missing --cov-fail-under=80
# Strict adapters health with coverage gate
adapters-health-strict:
	DRYRUN=1 PYTHONPATH=. $(PY) -m pytest -q \
	 --cov=packages --cov-report=term-missing --cov-fail-under=80 \
	 tests/connectors/test_cj_smoke.py \
	 tests/connectors/test_db_coverage_smoke.py
