# FlowOS — Gym Management SaaS Backend

A Python/FastAPI backend for gym operations management supporting leads, members, classes, payments, and staff coordination.

## Quick Start

### 1. Setup

```bash
# Copy env
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Start with Docker
docker-compose up
```

App runs on `http://localhost:8000`  
API docs: `http://localhost:8000/docs`

### 2. Initialize Database

```bash
# Run migrations
alembic upgrade head
```

### 3. Create First Organization

```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Gym",
    "slug": "my-gym",
    "owner_email": "owner@gym.com"
  }'
```

## Architecture

### Tech Stack
- **Framework:** FastAPI 0.115
- **Database:** PostgreSQL 16 + SQLModel
- **ORM:** SQLAlchemy 2.0
- **Auth:** JWT + bcrypt
- **Migrations:** Alembic

### Data Model (14 entities)

```
organization → branch → staff (role-based)
                     ↓
                   leads → members
                              ↓
                        membership_plan
                        member_subscription
                              ↓
                           payments
                           
                        class_type
                        class_session → class_enrollment
                                             ↓
                                        attendance
                        
                        notification_log
```

### Modules

| Module | Purpose |
|--------|---------|
| `auth` | JWT login, token refresh, profile |
| `organizations` | Org setup (bootstrap) |
| `branches` | Multi-branch support |
| `staff` | Staff/trainer management |
| `leads` | Lead funnel (new → converted) |
| `members` | Member profiles + status |
| `plans` | Membership plan templates |
| `subscriptions` | Member subscriptions (pause/renew) |
| `payments` | Payment recording + dues tracking |
| `sessions` | Class sessions + enrollment |
| `attendance` | Gym check-ins + class attendance |
| `dashboard` | KPI aggregates + reports |
| `notifications` | Log-based notification system |

## API Overview

All endpoints under `/api/v1`

### Auth
- `POST /auth/login` — Get JWT tokens
- `POST /auth/refresh` — Refresh access token
- `GET /auth/me` — Current user profile

### Leads
- `POST /leads` — Create lead
- `GET /leads` — List leads
- `POST /leads/{id}/schedule-trial` — Schedule trial
- `POST /leads/{id}/convert` — Convert to member

### Members
- `POST /members` — Create member
- `GET /members` — List members
- `POST /members/{id}/pause` — Pause subscription

### Subscriptions
- `POST /subscriptions` — Create subscription
- `POST /subscriptions/{id}/renew` — Renew subscription

### Payments
- `POST /payments` — Record payment
- `GET /payments/summary` — Collections summary

### Classes
- `POST /sessions` — Schedule class
- `POST /sessions/{id}/enroll` — Enroll member
- `POST /sessions/{id}/attendance` — Mark attendance

### Dashboard
- `GET /dashboard/summary` — KPI snapshot
- `GET /dashboard/revenue` — Revenue report
- `GET /dashboard/dues` — Outstanding dues

## Development

### Run Tests
```bash
pytest tests/
```

### Code Quality
```bash
black app/
ruff check app/
```

### Database Migrations

Create migration:
```bash
alembic revision --autogenerate -m "add field"
```

Run migrations:
```bash
alembic upgrade head
```

## Roles & Permissions

| Role | Permissions |
|------|-------------|
| `owner` | Full access + org/branch admin |
| `branch_manager` | Branch-level + staff management |
| `front_desk` | Lead/member/payment entry + attendance |
| `trainer` | Class list, attendance marking, own schedule |
| `member` | Self-service (deferred for POC) |

## Features

✅ **Phase 1:** Infrastructure + config  
✅ **Phase 2:** Auth + org/branch/staff  
✅ **Phase 3-4:** Leads, members, plans, subscriptions  
✅ **Phase 5-6:** Payments, classes, attendance  
✅ **Phase 7:** Dashboard, notifications (log-only)  
✅ **Phase 8:** Polish, tests, utilities  

## Next Steps

1. Integrate with WhatsApp/SMS provider for notifications
2. Add member self-service portal
3. Implement advanced reporting/analytics
4. Multi-branch billing aggregation
5. Payment gateway integration (Stripe, Razorpay, etc.)

---

Built with ❤️ for gym management
