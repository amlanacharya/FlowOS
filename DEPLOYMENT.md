# FlowOS Deployment Guide

## Local Development

### Prerequisites
- Python 3.12+
- Docker & docker-compose
- PostgreSQL client tools (psql) — optional

### Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd FlowOS
cp .env.example .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start services
docker-compose up

# 4. Verify build
python verify_build.py

# 5. Run migrations
alembic upgrade head

# 6. Access API
# Open http://localhost:8000/docs
```

## Docker Setup

### docker-compose.yml Services

**postgres** (PostgreSQL 16)
- Port: 5432
- Default user: `flowos`
- Default password: `flowos_dev_pass`
- Database: `flowos_db`
- Volume: `postgres_data/` (persisted)

**app** (FastAPI)
- Port: 8000
- Hot-reload enabled (code changes auto-restart)
- Depends on: postgres (waits for healthcheck)

### Environment Variables

Copy `.env.example` → `.env`:
```
POSTGRES_USER=flowos
POSTGRES_PASSWORD=flowos_dev_pass
POSTGRES_DB=flowos_db
DATABASE_URL=postgresql://flowos:flowos_dev_pass@localhost:5432/flowos_db
SECRET_KEY=<64-char random string>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development
```

For production, use a secret management tool (AWS Secrets Manager, HashiCorp Vault, etc.).

## Database Migrations

### Create Database Schema

```bash
alembic upgrade head
```

### Create a New Migration

```bash
# Auto-detect model changes
alembic revision --autogenerate -m "add field_name"

# Or manually create
alembic revision -m "custom migration"
```

Edit the generated file in `alembic/versions/`, then apply:

```bash
alembic upgrade head
```

### Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

## API Setup

### Bootstrap Organization

```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Gym",
    "slug": "my-gym",
    "owner_email": "owner@gym.com",
    "phone": "1234567890"
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Gym",
  "slug": "my-gym",
  "owner_email": "owner@gym.com",
  "is_active": true,
  "created_at": "2026-04-23T12:00:00"
}
```

### Create Branch

```bash
curl -X POST "http://localhost:8000/api/v1/branches?org_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Branch",
    "address": "123 Fitness St",
    "city": "Fitness City",
    "phone": "1234567890"
  }'
```

### Create Owner Staff User

```bash
curl -X POST http://localhost:8000/api/v1/staff \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@gym.com",
    "password": "SecurePassword123!",
    "full_name": "Gym Owner",
    "phone": "1234567890",
    "role": "owner",
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "branch_id": "<branch_id_from_above>"
  }'
```

### Login and Get Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@gym.com",
    "password": "SecurePassword123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

Use `access_token` in subsequent requests:
```bash
curl -H "Authorization: Bearer eyJhbGc..." http://localhost:8000/api/v1/auth/me
```

## Production Deployment

### AWS ECS Deployment

1. **Build Docker image**
   ```bash
   docker build -t flowos-backend:latest .
   docker tag flowos-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/flowos-backend:latest
   docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/flowos-backend:latest
   ```

2. **RDS PostgreSQL**
   - Create RDS instance (PostgreSQL 16)
   - Update `DATABASE_URL` in ECS task definition
   - Run migrations: `alembic upgrade head`

3. **ECS Task Definition**
   ```json
   {
     "name": "flowos-backend",
     "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/flowos-backend:latest",
     "portMappings": [{"containerPort": 8000}],
     "environment": [
       {"name": "DATABASE_URL", "value": "postgresql://..."},
       {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
       {"name": "ENVIRONMENT", "value": "production"}
     ],
     "logConfiguration": {
       "logDriver": "awslogs",
       "options": {"awslogs-group": "/ecs/flowos-backend"}
     }
   }
   ```

4. **Load Balancer**
   - ALB or NLB pointing to ECS service
   - Health check: `GET /health`
   - Enable sticky sessions for JWT

### GCP Cloud Run Deployment

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/flowos-backend

# Deploy
gcloud run deploy flowos-backend \
  --image gcr.io/PROJECT_ID/flowos-backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=postgresql://... \
  --set-env-vars SECRET_KEY=... \
  --memory 1Gi \
  --cpu 2
```

### Environment Setup (Production)

```bash
# Use strong secrets
export SECRET_KEY=$(openssl rand -hex 32)

# Use production database
export DATABASE_URL=postgresql://prod_user:prod_pass@prod-db.example.com/flowos_db

# Enable compression, security headers
export ENVIRONMENT=production
```

## Monitoring & Logging

### Application Logs

```bash
# View logs from docker-compose
docker-compose logs -f app

# View logs from ECS
aws logs tail /ecs/flowos-backend --follow
```

### Health Checks

```bash
# Simple health check
curl http://localhost:8000/health

# Database connectivity check
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/dashboard/summary
```

### Metrics to Monitor

- **Response time**: `GET /docs` should respond in <100ms
- **Database connections**: Monitor connection pool
- **Disk usage**: PostgreSQL data volume
- **CPU/Memory**: App container resource usage
- **Error rate**: Monitor 4xx and 5xx responses

## Backup & Recovery

### PostgreSQL Backups

```bash
# Full backup
pg_dump -h localhost -U flowos -d flowos_db > backup.sql

# Restore
psql -h localhost -U flowos -d flowos_db < backup.sql
```

### Automated Backups (RDS)

- Enable automated backups (7-day retention minimum)
- Enable multi-AZ for high availability
- Test restore procedure regularly

## Scaling Considerations

- **Horizontal scaling**: Multiple app instances behind load balancer (stateless design)
- **Vertical scaling**: Increase RDS instance size as needed
- **Connection pooling**: Use PgBouncer or RDS proxy
- **Caching**: Add Redis for session/token caching
- **CDN**: CloudFront for static assets (if added)

## Security Checklist

- [ ] Change default PostgreSQL password
- [ ] Use HTTPS/TLS for all connections
- [ ] Enable VPC security groups (restrict database access)
- [ ] Rotate SECRET_KEY regularly
- [ ] Enable CloudTrail/audit logging
- [ ] Use secrets management (not hardcoded)
- [ ] Enable rate limiting (Slowapi)
- [ ] Set up DDoS protection (AWS Shield)
- [ ] Regular security audits and penetration testing
- [ ] Keep dependencies updated (`pip list --outdated`)
