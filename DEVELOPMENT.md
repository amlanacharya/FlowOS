# FlowOS Development Guide

## Project Structure

```
FlowOS/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings (env vars)
│   ├── database.py                # SQLModel engine + session
│   ├── deps.py                    # Dependency injection (auth, roles)
│   ├── core/
│   │   ├── enums.py              # All Enums
│   │   ├── security.py           # Password hash + JWT
│   │   └── exceptions.py         # Custom HTTP exceptions
│   ├── models/                    # SQLModel ORM models (14 entities)
│   ├── schemas/                   # Pydantic request/response models
│   ├── routers/                   # API endpoints (13 modules)
│   ├── services/                  # Business logic (8 services)
│   └── utils/                     # Helper utilities
├── alembic/                       # Database migrations
├── tests/                         # Pytest test files
├── docker-compose.yml             # Local dev stack
├── Dockerfile                     # App container image
├── requirements.txt               # Python dependencies
├── .env.example                   # Template env vars
├── README.md                      # Quick start
├── ARCHITECTURE.md                # System design
├── DEPLOYMENT.md                  # Prod deployment
├── DEVELOPMENT.md                 # This file
└── seed_data.py                   # Sample data generator
```

## Adding a New Feature

### Example: Add "Referral" functionality to members

#### 1. Update Data Model

Create or update `app/models/member.py`:
```python
class Member(SQLModel, table=True):
    # ... existing fields ...
    referrer_member_id: Optional[UUID] = Field(default=None, foreign_key="members.id")
    referral_code: str = Field(max_length=20, unique=True, index=True)
```

#### 2. Create Migration

```bash
alembic revision --autogenerate -m "add member referral fields"
```

Review and apply:
```bash
alembic upgrade head
```

#### 3. Update Schema

Add to `app/schemas/member.py`:
```python
class MemberResponse(SQLModel):
    # ... existing fields ...
    referrer_member_id: Optional[UUID]
    referral_code: str
```

#### 4. Enhance Service

Update `app/services/member_service.py`:
```python
def generate_referral_code(self, member_id: UUID) -> str:
    """Generate unique referral code."""
    import random, string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"REF-{code}"

def get_member_referrals(self, referrer_id: UUID) -> List[Member]:
    """Get all members referred by this member."""
    query = select(Member).where(Member.referrer_member_id == referrer_id)
    return self.session.exec(query).all()
```

#### 5. Add Router Endpoints

Add to `app/routers/members.py`:
```python
@router.get("/{member_id}/referrals", response_model=List[MemberResponse])
async def get_referrals(
    member_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.branch_manager, RoleEnum.owner)),
    session: Session = Depends(get_session),
):
    service = MemberService(session)
    return service.get_member_referrals(member_id)
```

#### 6. Write Tests

Add to `tests/test_members.py`:
```python
def test_referral_code_generation(session):
    service = MemberService(session)
    code = service.generate_referral_code(uuid4())
    assert code.startswith("REF-")
    assert len(code) == 12  # "REF-" + 8 chars
```

#### 7. Documentation

Update API docs (automatic via FastAPI) and ARCHITECTURE.md if needed.

## Common Development Tasks

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_members.py

# Specific test
pytest tests/test_members.py::test_create_member

# With coverage
pytest --cov=app tests/

# Verbose output
pytest -v tests/
```

### Database Queries

```python
# In a service
from sqlmodel import select

# Query
members = self.session.exec(
    select(Member)
    .where(Member.branch_id == branch_id)
    .where(Member.status == MemberStatusEnum.active)
).all()

# Filter and paginate
members = self.session.exec(
    select(Member)
    .where(Member.branch_id == branch_id)
    .offset(skip)
    .limit(limit)
).all()

# Aggregate
from sqlalchemy import func
total_revenue = self.session.exec(
    select(func.sum(Payment.amount))
    .where(Payment.branch_id == branch_id)
).first()
```

### Adding Authentication to Routes

```python
from app.deps import require_roles, get_branch_scope, get_current_user
from app.core.enums import RoleEnum

@router.post("/admin-action")
async def admin_action(
    data: AdminRequest,
    # Enforce role
    claims: dict = Depends(require_roles(RoleEnum.owner)),
    # Inject current user
    user: User = Depends(get_current_user),
    # Auto-scope to branch (unless owner)
    branch_id: UUID = Depends(get_branch_scope),
    session: Session = Depends(get_session),
):
    # ... route logic ...
```

### Pagination

All list endpoints use skip/limit:
```
GET /api/v1/members?skip=0&limit=50
```

In service:
```python
def list_members(self, branch_id: UUID, skip: int = 0, limit: int = 100):
    return self.session.exec(
        select(Member)
        .where(Member.branch_id == branch_id)
        .offset(skip)
        .limit(limit)
    ).all()
```

### Error Handling

```python
from app.core.exceptions import (
    InvalidCredentialsException,
    ResourceNotFoundException,
    InsufficientPermissionsException,
)

@router.get("/{member_id}")
async def get_member(member_id: UUID, session: Session = Depends(get_session)):
    member = session.get(Member, member_id)
    if not member:
        raise ResourceNotFoundException()
    return member
```

### Custom Business Logic

Always place in services, not routers:

```python
# Bad: Logic in router
@router.post("/members/{id}/pause")
async def pause_member(id: UUID, session: Session = Depends(get_session)):
    member = session.get(Member, id)
    member.status = "paused"  # ❌ Business logic in router
    session.commit()
    return member

# Good: Logic in service
class MemberService:
    def pause_member(self, member_id: UUID) -> Member:
        member = self.session.get(Member, member_id)
        member.status = MemberStatusEnum.paused
        self.session.commit()
        return member

@router.post("/members/{id}/pause")
async def pause_member(id: UUID, session: Session = Depends(get_session)):
    service = MemberService(session)
    return service.pause_member(id)
```

## Code Style

### Naming Conventions
- **Files**: snake_case (member.py, lead_service.py)
- **Classes**: PascalCase (Member, LeadService)
- **Functions/variables**: snake_case (create_member, member_id)
- **Constants**: UPPER_SNAKE_CASE (MAX_RETRIES, DEFAULT_LIMIT)
- **Routes**: kebab-case (/api/v1/class-types)

### Type Hints
Always use type hints:
```python
# Good
def create_member(self, branch_id: UUID, data: MemberCreate) -> Member:
    ...

# Bad
def create_member(self, branch_id, data):
    ...
```

### Imports
Organize by group:
```python
# 1. Standard library
from datetime import date, datetime
from uuid import UUID
from typing import List, Optional

# 2. Third-party
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

# 3. Local app
from app.models import Member
from app.schemas import MemberResponse
from app.core.enums import RoleEnum
```

### Documentation
Minimal comments (good code is self-documenting):
```python
# Only comment the WHY, not the WHAT

# Bad comment
def get_member(member_id: UUID):
    """Returns a member by id"""  # This is obvious from signature
    ...

# Good comment
def pause_member(self, member_id: UUID) -> Member:
    """Pause a member's subscription without cancelling.
    
    Used for gym closures or member temporary leave.
    Retains all history and renewal tracking.
    """
    ...
```

## Debugging

### Print Debugging

```python
# FastAPI/Uvicorn logs print to console
print(f"DEBUG: member_id={member_id}, status={member.status}")
```

### Debug with breakpoint()

```python
@router.get("/{member_id}")
async def get_member(member_id: UUID, session: Session = Depends(get_session)):
    member = session.get(Member, member_id)
    breakpoint()  # Execution pauses here
    return member
```

Stop the app with docker-compose, then run locally:
```bash
python -m uvicorn app.main:app --reload
```

### Database Inspection

```bash
# Connect to postgres
docker-compose exec db psql -U flowos -d flowos_db

# List tables
\dt

# Query directly
SELECT * FROM members LIMIT 5;
```

## Performance Tips

1. **Use indexes**: Defined in models on frequently-queried columns
   ```python
   branch_id: UUID = Field(foreign_key="branches.id", index=True)
   ```

2. **Avoid N+1 queries**: Load related data eagerly
   ```python
   # Bad: N+1 problem
   members = session.exec(select(Member)).all()
   for m in members:
       subs = session.exec(select(MemberSubscription).where(...)).all()  # Loop query!

   # Good: Single query
   subs = session.exec(select(MemberSubscription)).all()
   ```

3. **Use denormalized columns**: Pre-compute for fast reads
   - `member_subscription.amount_due` (updated with payments)
   - `class_session.enrolled_count` (updated with enrollments)

4. **Pagination**: Always limit result sets
   ```python
   query = query.offset(skip).limit(limit)
   ```

## Version Control

### Commit Messages
```
Add member referral functionality

- Generate unique referral codes
- Track referrers for commission tracking
- Add /members/{id}/referrals endpoint

Closes #123
```

### Branch Naming
```
feature/member-referrals
bugfix/payment-date-handling
chore/upgrade-fastapi
docs/deployment-guide
```

## Release Checklist

- [ ] All tests passing (`pytest tests/`)
- [ ] Code formatted (`black app/`)
- [ ] No linting errors (`ruff check app/`)
- [ ] Migrations tested (`alembic upgrade head`)
- [ ] OpenAPI docs updated (`/docs`)
- [ ] CHANGELOG.md updated
- [ ] Version bumped in pyproject.toml
- [ ] Git tag created (`git tag v1.2.0`)

---

Happy coding! 🚀
