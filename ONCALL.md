# MarketMind On-Call Guide (v1.0)

## On-Call Rotation
- **Primary**: rotating weekly; hours: 24x7
- **Secondary**: rotates with primary; step in on no-response in 15m
- **Paging**: PagerDuty / Slack #oncall
- **Hand-off**: notes in runbook; open incidents reviewed in weekly ops meeting

## SLAs
- **P0 Critical**: acknowledge 5m, resolve 60m
- **P1 High**: acknowledge 15m, resolve 4h  
- **P2 Medium**: acknowledge 1h, resolve 24h
- **P3 Low**: acknowledge 24h, resolve 1 week

## Escalation Contacts

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

### Management Escalation
- **Engineering Manager**: [Manager] - [Phone] - [Email]
- **CTO**: [CTO] - [Phone] - [Email]
- **CEO**: [CEO] - [Phone] - [Email]

## Incident Response Process

### 1. Acknowledge (< 5 minutes)
- [ ] Acknowledge alert in monitoring system
- [ ] Join #incident-response channel
- [ ] Post initial acknowledgment: "Investigating [brief description]"
- [ ] Check status page: https://status.marketmind.ai

### 2. Assess (< 10 minutes)
- [ ] Determine severity (P0-P3)
- [ ] Check recent deployments and changes
- [ ] Review error rates and response times
- [ ] Identify affected services and user impact

### 3. Communicate
- [ ] Update status page with initial findings
- [ ] Notify stakeholders based on severity
- [ ] Provide regular updates every 15-30 minutes
- [ ] Document actions taken in incident channel

### 4. Investigate & Mitigate
- **Monitoring**: https://grafana.marketmind.ai
- **Logs**: https://kibana.marketmind.ai  
- **Errors**: https://sentry.io/organizations/marketmind
- **APM**: https://apm.marketmind.ai

## Common Incident Playbooks

### API Down
```bash
# Check container status
kubectl get pods -n marketmind
docker-compose ps

# Check logs
kubectl logs deployment/marketmind-api -n marketmind
docker-compose logs api

# Restart if needed
kubectl rollout restart deployment/marketmind-api -n marketmind
docker-compose restart api
```

### Worker Queue Backlog
```bash
# Check queue depth
redis-cli -u $REDIS_URL llen celery

# Scale workers
kubectl scale deployment marketmind-worker --replicas=10 -n marketmind
docker-compose up -d --scale worker=10
```

### Database Issues
```bash
# Check connectivity
psql $DB_URL -c "SELECT 1;"

# Check connection pool
curl https://api.marketmind.ai/health/data

# Monitor metrics: connection count, query performance, disk space
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

## Emergency Contacts

### Internal Team
- **Engineering**: engineering@marketmind.ai
- **DevOps**: devops@marketmind.ai
- **Security**: security@marketmind.ai

### External Vendors
- **Cloud Provider**: [Support contact and priority level]
- **Database Service**: [Support contact and SLA]
- **Monitoring Service**: [Support contact]

### Customer Communication
- **Support**: support@marketmind.ai
- **Customer Success**: success@marketmind.ai
- **Status Page**: https://status.marketmind.ai

---

**Remember**: When in doubt, escalate early. Better to wake someone unnecessarily than let a critical issue persist.
