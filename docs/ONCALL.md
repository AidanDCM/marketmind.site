# MarketMind On-Call Guide

## Overview
This guide provides procedures for on-call engineers responding to MarketMind production incidents.

## On-Call Rotation

### Primary On-Call
- **Current**: [Your Name]
- **Phone**: [Your Phone]
- **Email**: [Your Email]
- **Slack**: @[your-handle]

### Secondary On-Call
- **Current**: [Backup Name]
- **Phone**: [Backup Phone]
- **Email**: [Backup Email]
- **Slack**: @[backup-handle]

### Escalation Contacts
- **Engineering Manager**: [Manager Name] - [Phone] - [Email]
- **CTO**: [CTO Name] - [Phone] - [Email]
- **CEO**: [CEO Name] - [Phone] - [Email]

## Incident Response Procedures

### 1. Incident Acknowledgment (< 5 minutes)
- [ ] Acknowledge alert in monitoring system (PagerDuty/OpsGenie)
- [ ] Join incident response channel: `#incident-response`
- [ ] Post initial acknowledgment: "Investigating [brief description]"
- [ ] Check status page: https://status.marketmind.ai

### 2. Initial Assessment (< 10 minutes)
- [ ] Determine incident severity (P0-P3)
- [ ] Check recent deployments and changes
- [ ] Review error rates and response times
- [ ] Identify affected services and user impact

### 3. Communication
- [ ] Update status page with initial findings
- [ ] Notify stakeholders based on severity
- [ ] Provide regular updates every 15-30 minutes
- [ ] Document actions taken in incident channel

### 4. Investigation Tools
- **Monitoring**: https://grafana.marketmind.ai
- **Logs**: https://kibana.marketmind.ai
- **Errors**: https://sentry.io/organizations/marketmind
- **APM**: https://apm.marketmind.ai

## Severity Levels

### P0 - Critical (Page Immediately)
- **Definition**: Complete service outage or data loss
- **Response Time**: 5 minutes
- **Escalation**: Immediate to engineering manager
- **Communication**: Status page + customer notification

**Examples**:
- API completely down
- Database corruption
- Security breach
- Payment processing failure

### P1 - High (Page During Business Hours)
- **Definition**: Major feature broken, significant user impact
- **Response Time**: 15 minutes
- **Escalation**: 30 minutes if no progress
- **Communication**: Status page update

**Examples**:
- Authentication failures
- Core workflow broken
- Performance degradation >50%
- Third-party integration failures

### P2 - Medium (Alert Only)
- **Definition**: Minor feature issues, limited user impact
- **Response Time**: 1 hour
- **Escalation**: Next business day
- **Communication**: Internal only

**Examples**:
- Non-critical feature bugs
- Performance degradation <25%
- Monitoring alerts
- Queue backlog

### P3 - Low (Ticket Only)
- **Definition**: Cosmetic issues, no user impact
- **Response Time**: Next business day
- **Escalation**: Not required
- **Communication**: Internal ticket

## Common Incident Types

### API Not Responding
```bash
# Check container status
kubectl get pods -n marketmind
docker ps | grep marketmind

# Check logs
kubectl logs -f deployment/marketmind-api -n marketmind
docker logs marketmind-api

# Check health endpoint
curl https://api.marketmind.ai/health/summary

# Restart if needed
kubectl rollout restart deployment/marketmind-api -n marketmind
docker restart marketmind-api
```

### Database Issues
```bash
# Check database connectivity
psql $DB_URL -c "SELECT 1;"

# Check connection pool
curl https://api.marketmind.ai/health/data

# Check database metrics
# - Connection count
# - Query performance
# - Disk space
# - Memory usage
```

### Worker Queue Backlog
```bash
# Check queue depths
redis-cli -u $REDIS_URL llen celery

# Check worker status
celery -A apps.hive_worker.celery_app.app inspect active
celery -A apps.hive_worker.celery_app.app inspect stats

# Scale workers
kubectl scale deployment marketmind-worker --replicas=10 -n marketmind
docker-compose up --scale worker=5
```

### High Error Rate
1. Check Sentry dashboard for error patterns
2. Review recent deployments and changes
3. Check external service dependencies
4. Consider rolling back if deployment-related
5. Scale resources if capacity-related

## Rollback Procedures

### Application Rollback
```bash
# Kubernetes
kubectl rollout undo deployment/marketmind-api -n marketmind
kubectl rollout status deployment/marketmind-api -n marketmind

# Docker
docker tag marketmind/api:v1.0.1 marketmind/api:latest
docker-compose up -d api

# Verify health after rollback
curl https://api.marketmind.ai/health/summary
```

### Database Rollback
```bash
# CAUTION: May cause data loss
# Always test in staging first
.venv/bin/python scripts/alembic_cli.py downgrade -1

# Verify application compatibility
make verify-integrations
```

## Post-Incident Actions

### Immediate (< 2 hours)
- [ ] Confirm incident is fully resolved
- [ ] Update status page with resolution
- [ ] Notify stakeholders of resolution
- [ ] Document timeline and actions taken

### Follow-up (< 24 hours)
- [ ] Write post-mortem document
- [ ] Identify root cause and contributing factors
- [ ] Create action items to prevent recurrence
- [ ] Schedule post-mortem review meeting

### Long-term (< 1 week)
- [ ] Implement preventive measures
- [ ] Update monitoring and alerting
- [ ] Update runbooks and procedures
- [ ] Share learnings with team

## Emergency Contacts

### Internal Team
- **Engineering Team**: engineering@marketmind.ai
- **DevOps Team**: devops@marketmind.ai
- **Security Team**: security@marketmind.ai

### External Vendors
- **Cloud Provider**: [Support contact and priority level]
- **Database Service**: [Support contact and SLA]
- **Monitoring Service**: [Support contact]
- **CDN Provider**: [Support contact]

### Customer Communication
- **Support Team**: support@marketmind.ai
- **Customer Success**: success@marketmind.ai
- **Status Page**: https://status.marketmind.ai

## Useful Commands

### Health Checks
```bash
# API health
curl https://api.marketmind.ai/health/summary

# Database connectivity
psql $DB_URL -c "SELECT version();"

# Redis connectivity
redis-cli -u $REDIS_URL ping

# Worker status
celery -A apps.hive_worker.celery_app.app inspect ping
```

### Monitoring
```bash
# View recent logs
kubectl logs --tail=100 deployment/marketmind-api -n marketmind
docker logs --tail=100 marketmind-api

# Monitor metrics
curl https://api.marketmind.ai/metrics

# Check queue status
redis-cli -u $REDIS_URL llen celery
```

### Scaling
```bash
# Scale API
kubectl scale deployment marketmind-api --replicas=5 -n marketmind

# Scale workers
kubectl scale deployment marketmind-worker --replicas=10 -n marketmind

# Check resource usage
kubectl top pods -n marketmind
```

## Incident Response Checklist

### During Incident
- [ ] Acknowledge alert within 5 minutes
- [ ] Determine severity and impact
- [ ] Start incident response channel
- [ ] Update status page
- [ ] Notify stakeholders
- [ ] Investigate and mitigate
- [ ] Provide regular updates
- [ ] Document all actions

### After Resolution
- [ ] Confirm full resolution
- [ ] Update status page
- [ ] Notify stakeholders
- [ ] Write incident summary
- [ ] Schedule post-mortem
- [ ] Create follow-up tasks

## Training and Resources

### Required Reading
- [MarketMind Architecture Overview](./RUNBOOK.md)
- [Deployment Procedures](./RUNBOOK.md#deployment-procedures)
- [Monitoring and Alerting Guide](./RUNBOOK.md#monitoring--alerting)

### Training Exercises
- Monthly incident response drills
- Quarterly disaster recovery tests
- Annual security incident simulations

### Documentation
- [Production Runbook](./RUNBOOK.md)
- [Privacy Policy](./PRIVACY_POLICY.md)
- [Terms of Service](./TERMS_OF_SERVICE.md)
- [Security Procedures](./secrets_runbook.md)

---

**Remember**: When in doubt, escalate early. It's better to wake someone up unnecessarily than to let a critical issue persist.
