# MarketMind Production Deployment Guide

## 🚀 Quick Start

MarketMind is now **100% production-ready**. This guide provides step-by-step instructions for deploying to production.

## ✅ Pre-Deployment Verification

Run the comprehensive production readiness check:

```bash
make production-ready
```

Expected output:
```
🎉 MarketMind is PRODUCTION READY!
✅ All security checks passed
✅ All infrastructure checks passed  
✅ Docker Compose configurations valid
✅ Ready for deployment
```

## 🏗️ Deployment Options

### Option 1: Docker Compose (Recommended for Single Node)

#### Development/Staging Deployment
```bash
# Clone repository
git clone <your-repo-url>
cd MarketMind

# Start all services with health checks
docker-compose up -d

# Verify all services are healthy
docker-compose ps
```

#### Production Deployment
```bash
# Set up production environment variables
cp .env.production.example .env.production
# Edit .env.production with your production values

# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
curl https://your-domain.com/health/summary
```

### Option 2: Kubernetes (Recommended for Multi-Node)

#### Prerequisites
- Kubernetes cluster (1.20+)
- kubectl configured
- External PostgreSQL and Redis services

#### Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace marketmind

# Create secrets
kubectl create secret generic marketmind-secrets \
  --from-literal=DB_URL="postgresql://..." \
  --from-literal=REDIS_URL="redis://..." \
  --from-literal=SECRET_KEY="your-secret-key" \
  --from-literal=SENTRY_DSN="https://..." \
  -n marketmind

# Deploy services
kubectl apply -f k8s/ -n marketmind

# Verify deployment
kubectl get pods -n marketmind
kubectl get services -n marketmind
```

## 🔧 Environment Configuration

### Required Environment Variables

Copy `.env.production.example` and configure:

```bash
# Core Configuration
APP_ENV=production
SECRET_KEY=<generate-strong-32-char-key>

# Database (External managed service recommended)
DB_URL=postgresql+psycopg2://user:pass@prod-db:5432/marketmind

# Redis (External managed service recommended)  
REDIS_URL=redis://prod-redis:6379/0

# Security
TRUSTED_HOSTS=api.marketmind.ai,marketmind.ai
CORS_ORIGINS=https://app.marketmind.ai,https://marketmind.ai

# Observability
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Feature Flags (Production)
SIMULATION_ENABLED=false
DEBUG=0
ALLOW_ALL_HOSTS=0
```

### Generate Strong Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🗄️ Database Setup

### Option 1: Managed Database Service (Recommended)
- **AWS RDS**: PostgreSQL 15+
- **Google Cloud SQL**: PostgreSQL 15+
- **Azure Database**: PostgreSQL 15+

### Option 2: Self-Managed PostgreSQL
```bash
# Create database and user
createdb marketmind_prod
createuser marketmind_user

# Run migrations
DB_URL="postgresql://..." make migrate-up
```

## 📊 Monitoring Setup

### Sentry Error Tracking
1. Create Sentry project at https://sentry.io
2. Get DSN from project settings
3. Set `SENTRY_DSN` environment variable

### Prometheus Metrics
- API metrics: `https://your-domain.com/metrics`
- Worker metrics: `http://worker:9091/metrics`

### Health Checks
- API health: `https://your-domain.com/health/summary`
- Database: `https://your-domain.com/health/data`

## 🔒 Security Checklist

### Pre-Deployment Security
- [ ] Strong `SECRET_KEY` generated and configured
- [ ] `TRUSTED_HOSTS` set to production domains only
- [ ] `CORS_ORIGINS` restricted to production domains
- [ ] All API credentials are production-ready
- [ ] TLS certificates configured and valid
- [ ] Database credentials secured
- [ ] Redis secured with authentication

### Post-Deployment Security
- [ ] Run security scan: `make security-check`
- [ ] Verify rate limiting works: test `/auth/token` endpoint
- [ ] Confirm HTTPS redirect works
- [ ] Test CORS restrictions
- [ ] Verify API docs are hidden in production

## 🚦 Health Monitoring

### Service Health Checks

All services include comprehensive health checks:

```yaml
# API Service
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/health/summary"]
  interval: 15s
  timeout: 5s
  retries: 5

# Worker Service  
healthcheck:
  test: ["CMD", "celery", "-A", "apps.hive_worker.celery_app.app", "inspect", "ping"]
  interval: 30s
  timeout: 10s
  retries: 5

# Beat Scheduler
healthcheck:
  test: ["CMD", "pgrep", "-f", "celery.*beat"]
  interval: 60s
  timeout: 10s
  retries: 3
```

### Monitoring Endpoints
- **API Health**: `GET /health/summary`
- **Database Health**: `GET /health/data`
- **Metrics**: `GET /metrics`
- **Worker Status**: Celery inspect commands

## 🔄 Deployment Process

### 1. Pre-Deployment
```bash
# Verify production readiness
make production-ready

# Run integration tests
make verify-integrations

# Check test coverage
make test-cov-80
```

### 2. Database Migration
```bash
# Backup current database
pg_dump $CURRENT_DB_URL > backup-$(date +%Y%m%d).sql

# Run migrations
DB_URL=$PRODUCTION_DB_URL make migrate-up

# Verify migration
DB_URL=$PRODUCTION_DB_URL .venv/bin/python scripts/alembic_cli.py current
```

### 3. Application Deployment
```bash
# Build and tag images
docker build -f infra/docker/hive-api.Dockerfile -t marketmind/api:v1.0.0 .
docker build -f infra/docker/hive-worker.Dockerfile -t marketmind/worker:v1.0.0 .
docker build -f infra/docker/hive-beat.Dockerfile -t marketmind/beat:v1.0.0 .

# Push to registry
docker push marketmind/api:v1.0.0
docker push marketmind/worker:v1.0.0
docker push marketmind/beat:v1.0.0

# Deploy with zero-downtime
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Post-Deployment Verification
```bash
# Verify all services are healthy
docker-compose ps

# Test API endpoints
curl https://your-domain.com/health/summary
curl https://your-domain.com/auth/token -X POST -d "username=test&password=test"

# Check worker status
docker-compose exec worker celery -A apps.hive_worker.celery_app.app inspect ping

# Monitor logs
docker-compose logs -f api worker beat
```

## 🔧 Troubleshooting

### Common Issues

#### API Not Starting
```bash
# Check logs
docker-compose logs api

# Common causes:
# - Database connection failed
# - Missing environment variables
# - Port already in use
```

#### Worker Not Processing Tasks
```bash
# Check worker logs
docker-compose logs worker

# Check Redis connection
docker-compose exec worker redis-cli -u $REDIS_URL ping

# Check queue status
docker-compose exec worker celery -A apps.hive_worker.celery_app.app inspect active
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose exec api psql $DB_URL -c "SELECT 1;"

# Check database health
curl https://your-domain.com/health/data
```

### Performance Tuning

#### API Scaling
```bash
# Scale API service
docker-compose up -d --scale api=3

# Or in Kubernetes
kubectl scale deployment marketmind-api --replicas=3
```

#### Worker Scaling
```bash
# Scale worker service
docker-compose up -d --scale worker=5

# Or in Kubernetes
kubectl scale deployment marketmind-worker --replicas=5
```

## 📋 Rollback Procedures

### Application Rollback
```bash
# Rollback to previous version
docker-compose -f docker-compose.prod.yml down
docker tag marketmind/api:v0.9.0 marketmind/api:latest
docker-compose -f docker-compose.prod.yml up -d

# Verify rollback
curl https://your-domain.com/health/summary
```

### Database Rollback
```bash
# CAUTION: Test in staging first
DB_URL=$PRODUCTION_DB_URL .venv/bin/python scripts/alembic_cli.py downgrade -1

# Verify application compatibility
make verify-integrations
```

## 📞 Support & Incident Response

### Emergency Contacts
- **On-Call Engineer**: See `docs/ONCALL.md`
- **Engineering Team**: engineering@marketmind.ai
- **DevOps Team**: devops@marketmind.ai

### Incident Response
1. Follow procedures in `docs/ONCALL.md`
2. Use `docs/RUNBOOK.md` for operational procedures
3. Update status page during incidents
4. Document all actions taken

## 🎯 Success Metrics

### Deployment Success Indicators
- [ ] All health checks passing
- [ ] API response time < 500ms P95
- [ ] Error rate < 1%
- [ ] All workers responding to ping
- [ ] Database queries executing normally
- [ ] Scheduled tasks running on schedule

### Monitoring Dashboards
- **Sentry**: Error tracking and performance
- **Prometheus/Grafana**: Infrastructure metrics
- **Application Logs**: Structured JSON logs
- **Business Metrics**: Custom dashboards

---

## 🎉 Congratulations!

MarketMind is now successfully deployed to production with:

✅ **Enterprise-grade security**  
✅ **Production-hardened infrastructure**  
✅ **Comprehensive monitoring**  
✅ **Automated health checks**  
✅ **Professional operational procedures**

Your e-commerce automation platform is ready to scale and serve real customers!
