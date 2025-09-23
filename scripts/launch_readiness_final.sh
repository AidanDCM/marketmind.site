#!/bin/bash

# MarketMind Final Launch Readiness Check
# Verifies all critical production requirements are met

set -e

echo "🚀 MarketMind Final Launch Readiness Check"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED_CHECKS=0
TOTAL_CHECKS=0

check_result() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

echo ""
echo "🔒 CRITICAL SECURITY CHECKS"
echo "----------------------------"

# Check 1: No .git directory in production build
if [ ! -d ".git" ]; then
    check_result 0 "No .git directory present"
else
    check_result 1 "CRITICAL: .git directory found - remove from production builds"
fi

# Check 2: No real .env files
if [ ! -f ".env" ] && [ ! -f ".env.bak" ]; then
    check_result 0 "No real .env files present"
else
    check_result 1 "CRITICAL: Real .env files found - use secrets manager in production"
fi

# Check 3: .dockerignore exists and contains security exclusions
if [ -f ".dockerignore" ] && grep -q ".git" .dockerignore && grep -q ".env" .dockerignore; then
    check_result 0 ".dockerignore properly configured"
else
    check_result 1 ".dockerignore missing or incomplete"
fi

# Check 4: Production environment template exists
if [ -f ".env.production.example" ]; then
    check_result 0 "Production environment template exists"
else
    check_result 1 "Production environment template missing"
fi

echo ""
echo "🏗️  INFRASTRUCTURE CHECKS"
echo "-------------------------"

# Check 5: API Dockerfile uses non-root user
if grep -q "USER appuser" infra/docker/hive-api.Dockerfile; then
    check_result 0 "API runs as non-root user"
else
    check_result 1 "API Dockerfile missing non-root user"
fi

# Check 6: Worker Dockerfile uses non-root user
if grep -q "USER app" infra/docker/hive-worker.Dockerfile; then
    check_result 0 "Worker runs as non-root user"
else
    check_result 1 "Worker Dockerfile missing non-root user"
fi

# Check 7: Beat separated from worker
if ! grep -q "\-B" infra/docker/hive-worker.Dockerfile; then
    check_result 0 "Beat separated from worker"
else
    check_result 1 "Beat still coupled with worker (-B flag found)"
fi

# Check 8: Beat container exists
if [ -f "infra/docker/hive-beat.Dockerfile" ]; then
    check_result 0 "Separate Beat container defined"
else
    check_result 1 "Beat container Dockerfile missing"
fi

echo ""
echo "🔐 AUTHENTICATION & RATE LIMITING"
echo "----------------------------------"

# Check 9: Rate limiting on auth endpoint
if grep -q "limiter.limit.*5/minute" apps/hive_api/routers/auth.py; then
    check_result 0 "Auth endpoint rate limited"
else
    check_result 1 "Auth endpoint missing rate limiting"
fi

# Check 10: TrustedHostMiddleware configured
if grep -q "TrustedHostMiddleware" apps/hive_api/main.py; then
    check_result 0 "TrustedHostMiddleware configured"
else
    check_result 1 "TrustedHostMiddleware missing"
fi

echo ""
echo "📊 OBSERVABILITY & MONITORING"
echo "------------------------------"

# Check 11: Sentry integration in API
if grep -q "sentry_sdk" apps/hive_api/main.py; then
    check_result 0 "Sentry integrated in API"
else
    check_result 1 "Sentry missing from API"
fi

# Check 12: Sentry integration in Worker
if grep -q "sentry_sdk" apps/hive_worker/celery_app.py; then
    check_result 0 "Sentry integrated in Worker"
else
    check_result 1 "Sentry missing from Worker"
fi

# Check 13: Prometheus metrics endpoint
if grep -q "/metrics" apps/hive_api/main.py; then
    check_result 0 "Prometheus metrics endpoint configured"
else
    check_result 1 "Prometheus metrics endpoint missing"
fi

# Check 14: OpenTelemetry instrumentation
if grep -q "FastAPIInstrumentor" apps/hive_api/main.py; then
    check_result 0 "OpenTelemetry instrumentation configured"
else
    check_result 1 "OpenTelemetry instrumentation missing"
fi

echo ""
echo "⚙️  CELERY TASK ROBUSTNESS"
echo "--------------------------"

# Check 15: Celery acks_late configured
if grep -q "task_acks_late=True" apps/hive_worker/celery_app.py; then
    check_result 0 "Celery acks_late configured"
else
    check_result 1 "Celery acks_late missing"
fi

# Check 16: Task retry configuration
if grep -q "task_max_retries" apps/hive_worker/celery_app.py; then
    check_result 0 "Task retry configuration present"
else
    check_result 1 "Task retry configuration missing"
fi

# Check 17: Worker recycling configured
if grep -q "worker_max_tasks_per_child" apps/hive_worker/celery_app.py; then
    check_result 0 "Worker recycling configured"
else
    check_result 1 "Worker recycling missing"
fi

echo ""
echo "🧪 TESTING & COVERAGE"
echo "----------------------"

# Check 18: No zero coverage gates
if ! grep -q "cov-fail-under=0" Makefile; then
    check_result 0 "No zero coverage gates found"
else
    check_result 1 "Zero coverage gate found in Makefile"
fi

# Check 19: 80% coverage requirement
if grep -q "cov-fail-under=80" Makefile; then
    check_result 0 "80% coverage requirement enforced"
else
    check_result 1 "80% coverage requirement missing"
fi

echo ""
echo "🌐 FRONTEND SECURITY"
echo "--------------------"

# Check 20: Next.js security headers
if grep -q "Content-Security-Policy" apps/console/next.config.js; then
    check_result 0 "Frontend CSP headers configured"
else
    check_result 1 "Frontend CSP headers missing"
fi

# Check 21: Production docs disabled
if grep -q '"docs_url": None' apps/hive_api/main.py && grep -q 'settings.env == "production"' apps/hive_api/main.py; then
    check_result 0 "API docs disabled in production"
else
    check_result 1 "API docs not disabled in production"
fi

echo ""
echo "📋 CI/CD PIPELINE"
echo "-----------------"

# Check 22: GitHub Actions workflow exists
if [ -f ".github/workflows/ci-cd.yml" ]; then
    check_result 0 "CI/CD pipeline configured"
else
    check_result 1 "CI/CD pipeline missing"
fi

# Check 23: Security scanning in CI
if grep -q "trivy" .github/workflows/ci-cd.yml; then
    check_result 0 "Security scanning in CI"
else
    check_result 1 "Security scanning missing from CI"
fi

# Check 24: Docker build in CI
if grep -q "docker/build-push-action" .github/workflows/ci-cd.yml; then
    check_result 0 "Docker build in CI pipeline"
else
    check_result 1 "Docker build missing from CI"
fi

echo ""
echo "📄 LEGAL & COMPLIANCE"
echo "----------------------"

# Check 25: License file exists
if [ -f "LICENSE" ]; then
    check_result 0 "LICENSE file present"
else
    check_result 1 "LICENSE file missing"
fi

# Check 26: Privacy Policy exists
if [ -f "docs/PRIVACY_POLICY.md" ]; then
    check_result 0 "Privacy Policy documented"
else
    check_result 1 "Privacy Policy missing"
fi

# Check 27: Terms of Service exists
if [ -f "docs/TERMS_OF_SERVICE.md" ]; then
    check_result 0 "Terms of Service documented"
else
    check_result 1 "Terms of Service missing"
fi

# Check 28: Operational runbook exists
if [ -f "docs/RUNBOOK.md" ]; then
    check_result 0 "Operational runbook present"
else
    check_result 1 "Operational runbook missing"
fi

echo ""
echo "🏗️  DIRECTORY STRUCTURE"
echo "-----------------------"

# Check 29: No duplicate worker directories
if [ ! -d "apps/hive-worker" ]; then
    check_result 0 "No duplicate worker directories"
else
    check_result 1 "Duplicate hive-worker directory found"
fi

# Check 30: No duplicate API directories
if [ ! -d "apps/hive-api" ]; then
    check_result 0 "No duplicate API directories"
else
    check_result 1 "Duplicate hive-api directory found"
fi

echo ""
echo "📊 FINAL RESULTS"
echo "================"

PASSED_CHECKS=$((TOTAL_CHECKS - FAILED_CHECKS))
PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo "Total Checks: $TOTAL_CHECKS"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"
echo "Pass Rate: $PASS_RATE%"

echo ""
if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED! MarketMind is PRODUCTION READY! 🎉${NC}"
    echo ""
    echo "✅ Security hardened"
    echo "✅ Infrastructure production-ready"
    echo "✅ Observability configured"
    echo "✅ Legal compliance in place"
    echo "✅ CI/CD pipeline operational"
    echo ""
    echo "🚀 Ready for confident production launch!"
    exit 0
elif [ $FAILED_CHECKS -le 3 ]; then
    echo -e "${YELLOW}⚠️  MOSTLY READY - Fix $FAILED_CHECKS remaining issues${NC}"
    exit 1
else
    echo -e "${RED}❌ NOT READY FOR PRODUCTION - $FAILED_CHECKS critical issues remain${NC}"
    echo ""
    echo "Please address the failed checks above before launching."
    exit 1
fi
