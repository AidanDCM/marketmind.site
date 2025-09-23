# MarketMind Production Runbook

## Overview
This runbook provides operational procedures for MarketMind production deployment, monitoring, and incident response.

## Architecture Overview
- **API**: FastAPI application with Gunicorn workers
- **Worker**: Celery task processing with Redis broker
- **Database**: PostgreSQL with Alembic migrations
- **Cache/Queue**: Redis for caching and task queues
- **Monitoring**: Sentry, OpenTelemetry, Prometheus metrics

## Pre-Deployment Checklist

### Environment Setup
- [ ] Copy `.env.production.example` to `.env.production`
- [ ] Configure all required secrets and API keys
- [ ] Set `APP_ENV=production` and `SIMULATION_ENABLED=false`
- [ ] Configure database connection string for production PostgreSQL
- [ ] Set up Redis cluster/managed service
- [ ] Configure Sentry DSN for error tracking

### Security Validation
- [ ] Verify strong `SECRET_KEY` is configured
- [ ] Confirm CORS origins are restricted to production domains
- [ ] Validate all API credentials are production-ready
- [ ] Ensure TLS certificates are valid and configured
- [ ] Run security scan: `make security-check`

### Launch Readiness
- [ ] Run launch readiness script: `make launch-readiness`
- [ ] Verify all integration tests pass: 33/33 PASS
- [ ] Confirm database migrations are up to date
- [ ] Test API health endpoints respond correctly
- [ ] Validate worker queues are operational

## Deployment Procedures

### Database Migration
```bash
# Run migrations (safe, idempotent)
make migrate-up

# Verify migration status
.venv/bin/python scripts/alembic_cli.py current
```

### Application Deployment
```bash
# Build production Docker images
docker build -f infra/docker/hive-api.Dockerfile -t marketmind/api:latest .
docker build -f infra/docker/hive-worker.Dockerfile -t marketmind/worker:latest .

# Deploy with orchestrator (K8s/Docker Compose)
# Ensure health checks pass before routing traffic
```

### Post-Deployment Verification
```bash
# Run comprehensive integration tests
make verify-integrations

# Check all phase systems
make all-phases-backtest

# Monitor error rates and response times
curl https://your-domain.com/metrics
```

## Monitoring & Alerting

### Key Metrics to Monitor
- **API Response Time**: P95 < 500ms, P99 < 1s
- **Error Rate**: < 1% for 5xx errors
- **Database Connections**: < 80% of pool size
- **Queue Depth**: < 100 pending tasks per queue
- **Worker Health**: All workers responding to heartbeat

### Health Check Endpoints
- `GET /health/summary` - Overall system health
- `GET /health/data` - Database connectivity
- `GET /metrics` - Prometheus metrics
- `GET /orchestrator/health` - Core systems status

### Sentry Integration
- Production errors automatically tracked
- Configure alerts for high-severity issues
- Review error trends in Sentry dashboard

## Incident Response

### Severity Levels
- **P0 (Critical)**: Complete service outage
- **P1 (High)**: Major feature broken, significant user impact
- **P2 (Medium)**: Minor feature issues, limited user impact
- **P3 (Low)**: Cosmetic issues, no user impact

### P0 Incident Response
1. **Immediate Actions** (< 5 minutes)
   - Acknowledge incident in monitoring system
   - Check service status dashboard
   - Verify recent deployments/changes
   
2. **Investigation** (< 15 minutes)
   - Check Sentry for error spikes
   - Review application logs
   - Verify database and Redis connectivity
   - Check infrastructure metrics
   
3. **Mitigation** (< 30 minutes)
   - Rollback recent deployment if suspected cause
   - Scale up resources if capacity issue
   - Restart services if needed
   - Implement temporary workaround
   
4. **Communication**
   - Update status page
   - Notify stakeholders
   - Provide regular updates every 30 minutes

### Common Issues & Solutions

#### API Not Responding
```bash
# Check container status
docker ps | grep marketmind

# Check logs
docker logs marketmind-api

# Restart if needed
docker restart marketmind-api
```

#### Database Connection Issues
```bash
# Check database connectivity
psql $DB_URL -c "SELECT 1;"

# Check connection pool
curl https://your-domain.com/health/data
```

#### Worker Queue Backlog
```bash
# Check queue depths
redis-cli -u $REDIS_URL llen celery

# Scale workers
docker scale marketmind-worker=5
```

#### High Error Rate
1. Check Sentry dashboard for error patterns
2. Review recent code changes
3. Check external service dependencies
4. Consider rolling back if deployment-related

## Maintenance Procedures

### Regular Maintenance (Weekly)
- [ ] Review error logs and trends
- [ ] Check database performance metrics
- [ ] Verify backup integrity
- [ ] Update security patches
- [ ] Review capacity utilization

### Database Maintenance (Monthly)
- [ ] Analyze query performance
- [ ] Review and optimize slow queries
- [ ] Check index usage
- [ ] Vacuum and analyze tables
- [ ] Test backup restoration

### Security Updates (As Needed)
- [ ] Update dependencies with security patches
- [ ] Rotate API keys and secrets
- [ ] Review access logs for anomalies
- [ ] Update TLS certificates before expiry

## Rollback Procedures

### Application Rollback
```bash
# Rollback to previous Docker image
docker tag marketmind/api:v1.0.1 marketmind/api:latest
docker restart marketmind-api

# Verify health after rollback
make verify-integrations
```

### Database Rollback
```bash
# Rollback one migration (CAUTION: may lose data)
.venv/bin/python scripts/alembic_cli.py downgrade -1

# Always test rollback in staging first
```

## Contact Information

### On-Call Rotation
- **Primary**: [Your Name] - [phone] - [email]
- **Secondary**: [Backup Name] - [phone] - [email]
- **Escalation**: [Manager Name] - [phone] - [email]

### External Vendors
- **Cloud Provider**: [Support contact]
- **Database Service**: [Support contact]
- **Monitoring Service**: [Support contact]

## Useful Commands

```bash
# Check system status
make launch-readiness

# Run integration tests
make verify-integrations

# Check API health
curl https://your-domain.com/health/summary

# View recent logs
docker logs --tail=100 marketmind-api

# Connect to database
psql $DB_URL

# Monitor Redis queues
redis-cli -u $REDIS_URL monitor
```

## Emergency Contacts

- **Infrastructure Team**: infrastructure@company.com
- **Security Team**: security@company.com
- **Database Team**: dba@company.com
- **Executive Escalation**: cto@company.com

## Restore Drill Log (Disaster Recovery Evidence)

Run a scratch restore using the provided scripts, then record the evidence below. Perform this at least once prior to GA and quarterly thereafter.

Commands:
```bash
DB_URL=postgres://prod ./scripts/db/backup.sh
# note the generated file name: backup-YYYYMMDD-HHMMSS.sql

SRC_SQL=backup-YYYYMMDD-HHMMSS.sql \
TARGET_DB_URL=postgres://scratch-db-url \
./scripts/db/restore.sh
```

Receipt:
- When: 2025-09-19T18:42Z
- Operator: <name>
- Source: backup-YYYYMMDD-HHMMSS.sql
- Target: postgres://scratch-db-url
- Result: ✅ success (validated core tables present)
