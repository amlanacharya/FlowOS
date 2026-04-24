# FlowOS Pre-Deployment Checklist

## Local Development Checklist

### Environment Setup
- [ ] Python 3.12+ installed (`python3 --version`)
- [ ] Docker & docker-compose installed
- [ ] Git configured (`git config user.name`)
- [ ] Clone repository
- [ ] Create virtual environment (`python3 -m venv venv`)
- [ ] Activate venv (`source venv/bin/activate`)

### Dependencies & Configuration
- [ ] Copy `.env.example` → `.env`
- [ ] Review `.env` values (especially `SECRET_KEY`)
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Run build verification (`python verify_build.py`)

### Database Setup
- [ ] Start docker services (`docker-compose up`)
- [ ] Wait for postgres healthcheck to pass
- [ ] Run migrations (`alembic upgrade head`)
- [ ] Verify tables created (`docker-compose exec db psql -U flowos -d flowos_db -c "\\dt"`)
- [ ] Seed sample data (optional, `python seed_data.py`)

### API Testing
- [ ] Start app (`docker-compose up` should still be running)
- [ ] Health check passes (`curl http://localhost:8000/health`)
- [ ] OpenAPI docs available (`curl http://localhost:8000/docs`)
- [ ] Bootstrap organization (create test org via API)
- [ ] Create test branch
- [ ] Create test staff user
- [ ] Login and get JWT token
- [ ] Test authenticated endpoint

### Code Quality
- [ ] All tests pass (`pytest tests/`)
- [ ] Code is formatted (`black app/`)
- [ ] Linting passes (`ruff check app/`)
- [ ] No type errors (`mypy app/` if configured)
- [ ] No obvious security issues

---

## Pre-Production Checklist

### Security
- [ ] Change default database passwords
- [ ] Generate strong `SECRET_KEY` (`openssl rand -hex 32`)
- [ ] Enable HTTPS/TLS in load balancer
- [ ] Configure CORS properly (not allow_origins=["*"])
- [ ] Review role definitions (ensure least privilege)
- [ ] Enable rate limiting (Slowapi)
- [ ] Set up DDoS protection (AWS Shield, CloudFlare)
- [ ] Enable database encryption (RDS encryption at rest)
- [ ] Enable VPC and security groups
- [ ] Set up secrets management (AWS Secrets Manager, Vault)
- [ ] Review environment variables (no hardcoded secrets)
- [ ] Enable database backups and test restore
- [ ] Set up audit logging
- [ ] Review third-party dependencies for vulnerabilities

### Infrastructure
- [ ] Production database configured (RDS/Cloud SQL/managed PostgreSQL)
- [ ] Load balancer configured (ALB/NLB)
- [ ] Container registry setup (ECR/GCR/Docker Hub)
- [ ] CI/CD pipeline configured (GitHub Actions/GitLab CI)
- [ ] Logging configured (CloudWatch/Stackdriver/Loki)
- [ ] Monitoring configured (CloudWatch/Datadog/New Relic)
- [ ] Alerting configured (email/Slack/PagerDuty)
- [ ] DNS configured and tested
- [ ] CDN configured (optional, CloudFront/Cloudflare)

### Code & Deployment
- [ ] All tests passing in CI
- [ ] Code reviewed and approved
- [ ] Migrations tested on production-like database
- [ ] Rollback plan documented
- [ ] Deployment runbook created
- [ ] Feature flags configured (if needed)
- [ ] Database schema backup taken
- [ ] Environment-specific configs verified
- [ ] Secrets configured in production environment

### Performance & Reliability
- [ ] Database connection pooling configured
- [ ] Pagination implemented on all list endpoints
- [ ] Indexes created on key columns (branch_id, member_id, etc.)
- [ ] Query performance tested with production-like data volumes
- [ ] Caching layer configured (Redis for sessions, if needed)
- [ ] API response times measured (<200ms p95)
- [ ] Database metrics monitored (connections, query performance)
- [ ] Error rates monitored (<0.1%)
- [ ] Auto-scaling configured (if cloud-based)
- [ ] Multi-AZ setup for high availability

### Documentation
- [ ] README updated with correct URLs
- [ ] API documentation generated (`/docs`)
- [ ] Deployment documentation reviewed
- [ ] Runbook for common issues created
- [ ] Architecture documentation reviewed
- [ ] Database schema documented
- [ ] Data retention policies documented
- [ ] Disaster recovery plan documented

### Testing
- [ ] End-to-end tests passing
- [ ] Load testing completed (target: 100 req/sec)
- [ ] Database stress testing completed
- [ ] Security scanning completed (OWASP Top 10)
- [ ] Accessibility testing (if frontend connected)
- [ ] Performance testing under load
- [ ] Failover testing completed
- [ ] Data integrity checks passing

### Operations
- [ ] On-call rotation established
- [ ] Incident response plan documented
- [ ] Rollback procedures tested
- [ ] Data export procedures tested
- [ ] Compliance requirements reviewed (GDPR, CCPA, etc.)
- [ ] Data privacy policy updated
- [ ] Terms of service updated
- [ ] Support process established

---

## Deployment Day Checklist

### Pre-Deployment (1 hour before)
- [ ] Notify team of deployment
- [ ] Confirm all checklists above are complete
- [ ] Final smoke test on staging
- [ ] Have rollback plan ready
- [ ] Monitor dashboards are open
- [ ] Communication channel open (Slack, etc.)

### Deployment
- [ ] Build Docker image
- [ ] Push to container registry
- [ ] Update deployment manifest
- [ ] Deploy to production (blue-green or canary)
- [ ] Run smoke tests
- [ ] Monitor metrics (error rate, latency, CPU)
- [ ] Check logs for errors

### Post-Deployment (30 mins after)
- [ ] Verify all endpoints responding
- [ ] Check error rates (should be normal)
- [ ] Check database connections
- [ ] Spot-check a few API calls
- [ ] Verify user can login and use core flows
- [ ] Monitor for any anomalies
- [ ] Document any issues

### Post-Deployment (2 hours after)
- [ ] No escalated issues
- [ ] Performance metrics within range
- [ ] Error rates normal
- [ ] Database health check
- [ ] Create post-deployment summary
- [ ] Note any learnings for next deployment

---

## Rollback Checklist

If anything goes wrong:

1. [ ] Assess severity
2. [ ] Notify stakeholders
3. [ ] Stop deployments to other services
4. [ ] Identify root cause (logs, metrics)
5. [ ] Decision: rollback or fix-forward?

**If rollback:**
1. [ ] Revert to previous image tag
2. [ ] Update deployment manifest
3. [ ] Redeploy
4. [ ] Run smoke tests
5. [ ] Monitor for stability
6. [ ] Communicate status
7. [ ] Schedule post-mortem

---

## Maintenance Checklist (Monthly)

- [ ] Review and update dependencies
- [ ] Check security advisories
- [ ] Review error logs for patterns
- [ ] Verify backups are working
- [ ] Test restore procedure
- [ ] Review metrics for trends
- [ ] Check database storage usage
- [ ] Verify logging is operational
- [ ] Review on-call incidents
- [ ] Update documentation

---

## Security Audit (Quarterly)

- [ ] OWASP Top 10 assessment
- [ ] Penetration testing (if resources allow)
- [ ] Code review for security issues
- [ ] Dependency security audit (`pip-audit`)
- [ ] Access control review
- [ ] Encryption review (at rest, in transit)
- [ ] Audit log review
- [ ] Compliance review (GDPR, etc.)
- [ ] Update threat model
- [ ] Review incident history

---

## Ready to Deploy? 🚀

If all items above are checked, you're ready for production!

```
✅ All systems go!
```

For any issues, refer to:
- ARCHITECTURE.md — Understanding the system
- DEPLOYMENT.md — Detailed deployment guide
- DEVELOPMENT.md — Development practices
- README.md — Quick start
