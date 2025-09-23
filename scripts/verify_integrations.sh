#!/bin/bash

# Comprehensive integration verification script for MarketMind
# Tests all API endpoints, health checks, and integration points

set -e

API_BASE="http://127.0.0.1:8001"
TIMEOUT=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

run_post_test_auth() {
    local test_name="$1"
    local endpoint="$2"
    local payload="$3"
    local expected_status="${4:-200}"

    TESTS_RUN=$((TESTS_RUN + 1))
    log_info "Testing: $test_name"

    local token
    token=$(gen_dev_token)

    if response=$(curl -s -w "%{http_code}" --connect-timeout $TIMEOUT \
        -X POST "$API_BASE$endpoint" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $token" \
        -d "$payload" 2>/dev/null); then

        http_code="${response: -3}"
        body="${response%???}"

        if [ "$http_code" = "$expected_status" ]; then
            log_success "$test_name - HTTP $http_code"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            log_error "$test_name - Expected $expected_status, got $http_code"
            echo "Response: $body" | head -c 200
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        log_error "$test_name - Connection failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Optionally generate a dev JWT with admin role for endpoints requiring write RBAC
gen_dev_token() {
    .venv/bin/python - <<'PY'
from packages.shared.config import get_settings
from jose import jwt

s = get_settings()
payload = {"sub": "verify", "role": "admin", "brain_ids": ["*"]}
def get_secret_key(settings):
    # Prefer backward-compatible property, then nested auth, then direct attr
    for attr in ("SECRET_KEY",):
        try:
            return getattr(settings, attr)
        except Exception:
            pass
    try:
        return settings.auth.secret_key
    except Exception:
        pass
    try:
        return settings.secret_key
    except Exception:
        pass
    raise RuntimeError("Secret key not found in settings")

def get_algorithm(settings):
    for attr in ("ALGORITHM",):
        try:
            return getattr(settings, attr)
        except Exception:
            pass
    try:
        return settings.auth.algorithm
    except Exception:
        pass
    return "HS256"

secret = get_secret_key(s)
alg = get_algorithm(s)
print(jwt.encode(payload, secret, algorithm=alg))
PY
}

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="${3:-200}"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    log_info "Testing: $test_name"
    
    if response=$(curl -s -w "%{http_code}" --connect-timeout $TIMEOUT "$test_command" 2>/dev/null); then
        http_code="${response: -3}"
        body="${response%???}"
        
        if [ "$http_code" = "$expected_status" ]; then
            log_success "$test_name - HTTP $http_code"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            log_error "$test_name - Expected $expected_status, got $http_code"
            echo "Response: $body" | head -c 200
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        log_error "$test_name - Connection failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

run_post_test() {
    local test_name="$1"
    local endpoint="$2"
    local payload="$3"
    local expected_status="${4:-200}"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    log_info "Testing: $test_name"
    
    if response=$(curl -s -w "%{http_code}" --connect-timeout $TIMEOUT \
        -X POST "$API_BASE$endpoint" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>/dev/null); then
        
        http_code="${response: -3}"
        body="${response%???}"
        
        if [ "$http_code" = "$expected_status" ]; then
            log_success "$test_name - HTTP $http_code"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            log_error "$test_name - Expected $expected_status, got $http_code"
            echo "Response: $body" | head -c 200
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        log_error "$test_name - Connection failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

check_json_field() {
    local json="$1"
    local field="$2"
    local expected="$3"
    
    if command -v jq >/dev/null 2>&1; then
        actual=$(echo "$json" | jq -r ".$field" 2>/dev/null)
        if [ "$actual" = "$expected" ]; then
            return 0
        else
            log_warning "Field $field: expected '$expected', got '$actual'"
            return 1
        fi
    else
        # Fallback without jq
        if echo "$json" | grep -q "\"$field\".*$expected"; then
            return 0
        else
            log_warning "Field $field: expected '$expected' (grep check)"
            return 1
        fi
    fi
}

# Main verification function
main() {
    echo "=================================================="
    echo "MarketMind Integration Verification"
    echo "=================================================="
    echo
    
    # Check if API is running
    log_info "Checking if API is accessible at $API_BASE"
    if ! curl -s --connect-timeout 5 "$API_BASE/_info" >/dev/null 2>&1; then
        log_error "API is not accessible at $API_BASE"
        log_info "Please start the API with: make api-local"
        exit 1
    fi
    log_success "API is accessible"
    echo
    
    # Basic health checks
    echo "=== Basic Health Checks ==="
    run_test "Liveness probe" "$API_BASE/health/live"
    run_test "Readiness probe" "$API_BASE/health/ready"
    run_test "Data health" "$API_BASE/health/data"
    run_test "App info" "$API_BASE/_info"
    echo
    
    # Integration health checks
    echo "=== Integration Health Checks ==="
    run_test "Integration health" "$API_BASE/health/integrations"
    run_test "Health summary" "$API_BASE/health/summary"
    echo

    # Orchestrator checks (Phase 7)
    echo "=== Orchestrator Checks (Phase 7) ==="
    run_test "Orchestrator health" "$API_BASE/orchestrator/health"
    run_test "Orchestrator queues" "$API_BASE/orchestrator/queues"
    # Freeze/unfreeze pricing brain
    TESTS_RUN=$((TESTS_RUN + 1))
    log_info "Testing: Freeze pricing brain"
    if response=$(curl -s -w "%{http_code}" --connect-timeout $TIMEOUT \
        -X POST "$API_BASE/orchestrator/freeze/pricing?freeze=true" 2>/dev/null); then
        http_code="${response: -3}"
        if [ "$http_code" = "200" ]; then
            log_success "Freeze pricing - HTTP $http_code"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "Freeze pricing - Expected 200, got $http_code"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        log_error "Freeze pricing - Connection failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    TESTS_RUN=$((TESTS_RUN + 1))
    log_info "Testing: Unfreeze pricing brain"
    if response=$(curl -s -w "%{http_code}" --connect-timeout $TIMEOUT \
        -X POST "$API_BASE/orchestrator/freeze/pricing?freeze=false" 2>/dev/null); then
        http_code="${response: -3}"
        if [ "$http_code" = "200" ]; then
            log_success "Unfreeze pricing - HTTP $http_code"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "Unfreeze pricing - Expected 200, got $http_code"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        log_error "Unfreeze pricing - Connection failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Override acceptance check
    TESTS_RUN=$((TESTS_RUN + 1))
    log_info "Testing: Override acceptance"
    if response=$(curl -s -w "%{http_code}" --connect-timeout $TIMEOUT \
        -X POST "$API_BASE/orchestrator/override?brain=pricing&decision_id=dec-cli&new_value=42&reason=verify" 2>/dev/null); then
        http_code="${response: -3}"
        if [ "$http_code" = "200" ]; then
            log_success "Override accepted - HTTP $http_code"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "Override - Expected 200, got $http_code"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        log_error "Override - Connection failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo
    
    # Ingestion endpoints
    echo "=== Ingestion Endpoints ==="
    run_test "Ingestion status" "$API_BASE/ingest/status"
    run_test "Ingestion health" "$API_BASE/ingest/health"
    
    # Test catalog sync (should start background task)
    run_post_test "CJ catalog sync" "/ingest/run/catalog" '{"supplier":"cj"}'
    
    # Test pricing snapshot
    run_post_test "Pricing snapshot" "/ingest/run/pricing" '{"asins":["B08N5WRWNW"],"write_to_sheets":false}'
    
    # Test order pull (placeholder)
    run_post_test "Order pull" "/ingest/run/orders" '{"channel":"amazon"}'
    echo

    # Orders endpoints (Phase 8 stubs)
    echo "=== Orders Endpoints (Phase 8) ==="
    run_test "Get order detail (stub)" "$API_BASE/orders/1"
    run_post_test "Reprocess order (stub)" "/orders/1/reprocess" '{}'
    run_post_test "Route order (stub)" "/orders/1/route" '{}'
    run_post_test "Create PO (stub)" "/orders/1/po" '{}'
    run_post_test "Fulfill order (stub)" "/orders/1/fulfill" '{}'
    run_post_test "Open exception (stub)" "/orders/1/exception" '{"kind":"OOS","note":"test"}'
    run_test "Orders KPIs (stub)" "$API_BASE/orders/kpis"
    echo
    
    # Pricing endpoints (if available)
    echo "=== Pricing Endpoints ==="
    run_test "Pricing history" "$API_BASE/pricing/history?asin=B08N5WRWNW&limit=5"
    run_test "Pricing pending" "$API_BASE/pricing/pending?limit=5"
    run_test "Pricing approved" "$API_BASE/pricing/approved?limit=5"
    echo

    # Learning endpoints (Phase 15)
    echo "=== Learning Endpoints (Phase 15) ==="
    run_test "Learning health" "$API_BASE/learning/health"
    run_test "Learning models list" "$API_BASE/learning/models?limit=5"
    run_test "Learning metrics list" "$API_BASE/learning/metrics?limit=5"
    run_test "Learning drift reports" "$API_BASE/learning/drift?limit=5"
    run_test "Learning benchmarks" "$API_BASE/learning/benchmarks?limit=5"
    run_test "Learning rollouts" "$API_BASE/learning/rollouts?limit=5"

    # Expect 202 Accepted for retrain enqueue (requires admin/editor role)
    run_post_test_auth "Learning retrain enqueue" "/learning/models/retrain" '{"brain":"pricing","dataset_range":"30d"}' 202
    echo
    
    # Feature flag validation
    echo "=== Feature Flag Validation ==="
    log_info "Checking environment variables..."
    
    # Check critical environment variables
    if [ -n "$AMAZON_SP_API_CLIENT_ID" ]; then
        log_success "AMAZON_SP_API_CLIENT_ID is set"
    else
        log_warning "AMAZON_SP_API_CLIENT_ID is not set"
    fi
    
    if [ -n "$CJ_API_KEY" ]; then
        log_success "CJ_API_KEY is set"
    else
        log_warning "CJ_API_KEY is not set"
    fi
    
    if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        log_success "GOOGLE_APPLICATION_CREDENTIALS is set"
    else
        log_warning "GOOGLE_APPLICATION_CREDENTIALS is not set"
    fi
    echo

    # Dev DB bootstrap: ensure shared models tables exist (useful for SQLite/dev)
    .venv/bin/python - <<'PY'
try:
    from packages.shared.db import Base, get_engine
    import packages.shared.models_db  # noqa: F401  # register models
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("Dev DB bootstrap: ensured tables exist")
except Exception as e:
    print(f"Dev DB bootstrap skipped: {e}")
PY

    # Database checks
    echo "=== Database Checks ==="
    log_info "Checking database connectivity..."
    
    if .venv/bin/python -c "
import sys
sys.path.append('.')
try:
    from packages.shared.db import SessionLocal
    from packages.shared.models_db import Product
    db = SessionLocal()
    count = db.query(Product).count()
    db.close()
    print(f'Database accessible - {count} products found')
    exit(0)
except Exception as e:
    print(f'Database error: {e}')
    exit(1)
" 2>/dev/null; then
        log_success "Database connectivity verified"
    else
        log_error "Database connectivity failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo
    
    # Configuration validation
    echo "=== Configuration Validation ==="
    log_info "Validating configuration structure..."
    
    if .venv/bin/python -c "
import sys
sys.path.append('.')
try:
    from packages.shared.config import get_settings
    settings = get_settings()
    print(f'App environment: {settings.env}')
    print(f'Amazon mode: {settings.amazon.mode}')
    print(f'Simulation enabled: {settings.flags.simulation_enabled}')
    exit(0)
except Exception as e:
    print(f'Config error: {e}')
    exit(1)
" 2>/dev/null; then
        log_success "Configuration validation passed"
    else
        log_error "Configuration validation failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo
    
    # Security checks
    echo "=== Security Checks ==="
    log_info "Running basic security validation..."
    
    # Check for common security issues
    if [ -f ".env" ]; then
        if grep -q "change-me" .env 2>/dev/null; then
            log_warning "Default secrets found in .env file"
        else
            log_success "No obvious default secrets in .env"
        fi
    else
        log_info ".env file not found (using environment variables)"
    fi
    
    # Check file permissions on sensitive files
    if [ -f "secrets/service-account.json" ]; then
        perms=$(stat -f "%A" secrets/service-account.json 2>/dev/null || stat -c "%a" secrets/service-account.json 2>/dev/null)
        if [ "$perms" = "600" ] || [ "$perms" = "400" ]; then
            log_success "Service account file has secure permissions ($perms)"
        else
            log_warning "Service account file permissions should be 600 or 400 (current: $perms)"
        fi
    fi
    echo
    
    # Final summary
    echo "=================================================="
    echo "Verification Summary"
    echo "=================================================="
    echo "Tests run: $TESTS_RUN"
    echo "Tests passed: $TESTS_PASSED"
    echo "Tests failed: $TESTS_FAILED"
    echo
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "All tests passed! ✅"
        echo
        echo "Your MarketMind integration is ready for Phase 1 testing."
        echo "Next steps:"
        echo "1. Configure your API credentials in .env"
        echo "2. Run 'make ingest-catalog' to sync supplier data"
        echo "3. Run 'make ingest-pricing' to test pricing snapshots"
        echo "4. Monitor health with 'make health-summary'"
        exit 0
    else
        log_error "Some tests failed. Please review the errors above."
        echo
        echo "Common fixes:"
        echo "1. Ensure all required environment variables are set"
        echo "2. Check database connectivity"
        echo "3. Verify API credentials are valid"
        echo "4. Review logs for detailed error messages"
        exit 1
    fi
}

# Run main function
main "$@"
