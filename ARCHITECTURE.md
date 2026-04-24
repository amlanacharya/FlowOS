# FlowOS Architecture

## High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI App                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │              CORS Middleware                       │ │
│  │  (allows cross-origin requests for web + mobile)  │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │                    Routers                         │ │
│  │ (13 modules: auth, orgs, branches, staff, leads,  │ │
│  │  members, plans, subs, payments, sessions,        │ │
│  │  attendance, dashboard, notifications)            │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Dependency Injection Layer (deps.py)      │ │
│  │ • Token extraction & JWT decode                   │ │
│  │ • Current user resolution                         │ │
│  │ • Role-based access control (RBAC)                │ │
│  │ • Branch scope isolation                          │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Services Layer                        │ │
│  │ (8 services: auth, lead, member, subscription,    │ │
│  │  payment, class, attendance, dashboard,           │ │
│  │  notification)                                    │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │          SQLModel ORM Layer (models/)             │ │
│  │ (14 entities: org, branch, user, staff, lead,     │ │
│  │  member, plan, subscription, payment, class_*,   │ │
│  │  attendance, notification_log)                    │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │      SQLAlchemy/Alembic Database Layer            │ │
│  │       PostgreSQL 16 (docker-compose)              │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Request Flow

```
HTTP Request
    ↓
FastAPI Router (e.g., POST /api/v1/members)
    ↓
Dependency Injection (deps.py)
    • Extract Bearer token from header
    • Decode JWT → claims dict
    • Load User from DB
    • Check role in require_roles()
    • Resolve branch_id via get_branch_scope()
    ↓
Route Handler (e.g., create_member)
    • Validate input schema (Pydantic)
    • Call service layer
    ↓
Service Layer (e.g., MemberService)
    • Business logic (generate member_code, etc.)
    • Call ORM methods
    • Return domain objects
    ↓
ORM Layer (SQLModel)
    • Execute SQL via SQLAlchemy
    • Commit transaction
    ↓
PostgreSQL Database
    ↓
HTTP Response (JSON via Pydantic schema)
```

## Database Schema

### Core Entities

**Organization** (root)
- id, name, slug, owner_email, is_active, timestamps

**Branch** (multi-tenancy)
- id, organization_id, name, address, city, is_active, timestamps

**User** (authentication)
- id, email, hashed_password, full_name, phone, is_active, is_verified, last_login

**Staff** (authorization)
- id, user_id, org_id, **branch_id**, role (enum), is_active

### Operational Entities

**Lead** (sales funnel)
- id, **branch_id**, full_name, phone, status (enum), trial_scheduled_at, converted_member_id

**Member** (core entity)
- id, **branch_id**, full_name, phone, member_code (unique), status (enum), joined_at

**MembershipPlan** (template)
- id, **branch_id**, name, duration_days, price, max_freezes_allowed, includes_classes

**MemberSubscription** (instance)
- id, member_id, **branch_id**, plan_id, start_date, end_date, status (enum)
- amount_due (denormalized, updated atomically with payments)

**Payment**
- id, **branch_id**, member_id, subscription_id, amount, mode (enum), payment_date

**ClassType** (template)
- id, **branch_id**, name, duration_minutes

**ClassSession** (instance)
- id, **branch_id**, class_type_id, trainer_staff_id, scheduled_at
- enrolled_count (denormalized, updated atomically with enrollments)

**ClassEnrollment** (pivot)
- id, session_id, member_id, **branch_id**, attended, cancelled
- Unique constraint: (session_id, member_id)

**Attendance**
- id, **branch_id**, member_id, attendance_type (enum), checked_in_at, checked_out_at

**NotificationLog** (audit)
- id, **branch_id**, recipient_type, recipient_id, channel, event_type, payload (JSON), status

**RefreshToken** (auth utility)
- id, jti (unique), user_id, expires_at, revoked

## Key Architectural Decisions

### 1. Branch-Awareness
Every operational record has explicit **`branch_id` foreign key**. This enables:
- Single-query branch isolation (no implicit filtering through joins)
- Permission enforcement at the database level
- Efficient multi-branch scaling

### 2. Role-Based Access Control (RBAC)
- Roles defined in `RoleEnum`: owner, branch_manager, front_desk, trainer, member
- Enforced via `require_roles()` dependency in every route
- Owner role bypasses branch filtering (can see all branches via `?branch_id=` query param)

### 3. JWT Tokens
- **Access token** (15 min): stateless, includes user_id, email, role, org_id, branch_id
- **Refresh token** (7 days): stored in DB with `jti` for revocation
- Refresh tokens are blacklistable on logout

### 4. Service Layer
- All business logic in services/ (not in routers)
- Services are testable independently
- Routers are thin HTTP adapters

### 5. Denormalization
To avoid expensive aggregates in high-frequency queries:
- `member_subscription.amount_due` — updated atomically when payment recorded
- `class_session.enrolled_count` — updated atomically when member enrolls

### 6. Soft Deletes
Use `is_active=False` flag instead of `deleted_at` column for POC simplicity. Can upgrade to proper soft-delete pattern if audit trail needed.

### 7. Status Enums
Use PostgreSQL native enums (`PgEnum`) for type safety and smaller storage.

## Module Breakdown

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| **auth** | User authentication & token management | AuthService, login/refresh/logout endpoints |
| **orgs** | Organization bootstrap | Organization CRUD |
| **branches** | Multi-location support | Branch CRUD, branch scoping |
| **staff** | Staff/trainer management | Staff CRUD, role assignment |
| **leads** | Lead funnel & sales pipeline | LeadService, FSM transitions |
| **members** | Member profiles & lifecycle | MemberService, status management |
| **plans** | Membership plan templates | MembershipPlan CRUD |
| **subscriptions** | Member subscriptions | SubscriptionService, pause/renew |
| **payments** | Payment recording & dues tracking | PaymentService, amount_due updates |
| **sessions** | Class scheduling & enrollment | ClassService, capacity enforcement |
| **attendance** | Check-in & class attendance | AttendanceService, duplicate guards |
| **dashboard** | KPI aggregates & reports | DashboardService, SQL aggregates |
| **notifications** | Event logging (log-only for POC) | NotificationService, event triggers |

## Security Considerations

1. **Password Hashing**: bcrypt with automatic salt
2. **CSRF Protection**: Rely on SameSite cookies + CORS validation (no explicit tokens needed for state-changing requests in browsers; API clients responsible for CORS)
3. **SQL Injection**: Prevented by SQLAlchemy parameterized queries
4. **Rate Limiting**: Not yet implemented (add Slowapi for production)
5. **Input Validation**: Pydantic schemas validate all inputs
6. **Authorization**: Role + branch isolation enforced on every request
7. **Audit Trail**: NotificationLog provides basic audit; can enhance with audit tables

## Performance Optimizations

- Database indexes on `branch_id`, `member_id`, `status`, `created_at`, `scheduled_at`
- Denormalized `amount_due` and `enrolled_count` to avoid costly aggregates
- Pagination on all list endpoints (skip/limit)
- Connection pooling via SQLAlchemy engine

## Testing Strategy

- **Unit tests**: Services with mocked Session
- **Integration tests**: Full request/response flow with test database
- **Fixtures**: Pytest with SQLite in-memory DB for speed
- **Fixtures include**: Sample org, branch, user, staff for common test setup

## Deployment Readiness

✅ Environment-driven config (pydantic-settings)  
✅ Database migrations via Alembic  
✅ Docker + docker-compose for local dev  
✅ Health check endpoint  
✅ OpenAPI/Swagger docs at `/docs`  
✅ Proper error handling & status codes  
✅ CORS configured  
✅ Async/await throughout (scalable)  

## Next Steps (Post-MVP)

1. **Notifications**: Integrate with WhatsApp/SMS/Email providers
2. **Payment Gateway**: Stripe, Razorpay, UPI integration
3. **Analytics**: Extended reporting, member segmentation
4. **Frontend**: Web (React) + Android (Flutter/Kotlin)
5. **Rate Limiting**: Slowapi for DDoS protection
6. **Caching**: Redis for session/token caching
7. **API Versioning**: Header-based or URL-based versioning for backward compatibility
