# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FlowOS is a gym management SaaS with two main components:
- **Backend** (`/`): FastAPI + PostgreSQL, Python 3.12
- **Frontend** (`web/`): React + TypeScript + Vite

## Commands

### Backend

```bash
make setup          # First-time setup: install deps + copy .env
make up             # Start docker-compose (app + postgres)
make down           # Stop services
make logs           # Tail app logs
make migrate        # alembic upgrade head
make test           # pytest tests/ -v
make lint           # ruff check app/
make format         # black app/
make verify         # python verify_build.py (import sanity check)
```

Run a single test:
```bash
pytest tests/test_auth.py -v
pytest tests/ -k "test_login" -v
```

Create a migration:
```bash
alembic revision --autogenerate -m "add field"
```

### Frontend

```bash
cd web
npm install
npm run dev         # Dev server on http://localhost:5173
npm run build       # Production build
npm run lint        # ESLint
```

## Architecture

### Backend Request Flow

```
HTTP Request → FastAPI Router → deps.py (auth + RBAC + branch scope) → Service Layer → SQLModel ORM → PostgreSQL
```

- **`app/routers/`** — Thin HTTP adapters; validate input schemas, call services, return responses
- **`app/services/`** — All business logic lives here; services are independently testable
- **`app/models/`** — SQLModel entities (dual-use: ORM table + Pydantic schema base)
- **`app/schemas/`** — Request/response Pydantic schemas
- **`app/core/deps.py`** — Dependency injection: JWT decode → user resolution → `require_roles()` → `get_branch_scope()`
- **`app/core/security.py`** — JWT creation/decode, bcrypt password hashing

### Branch-Awareness (Critical Pattern)

Every operational record carries an explicit `branch_id` FK. All list/create routes resolve a `branch_id` via `get_branch_scope()` in `deps.py`. **Owners** can pass `?branch_id=` to query across branches; all other roles are locked to their assigned branch.

### RBAC

Roles: `owner > branch_manager > front_desk > trainer > member`

Every route uses `require_roles([...])` as a FastAPI dependency. The JWT payload includes `role`, `org_id`, and `branch_id` so role checks are stateless.

### Denormalized Counters

Two fields are updated atomically (not aggregated at query time):
- `member_subscription.amount_due` — decremented when a payment is recorded
- `class_session.enrolled_count` — incremented/decremented on enrollment changes

Always update these in the same transaction as the triggering operation.

### Frontend Architecture

- **`web/src/App.tsx`** — Root: owns auth state (`accessToken`, `refreshToken`, `profile`), persists to `localStorage` under `flowos-*` keys, renders page routing
- **`web/src/api.ts`** — Single `apiFetch<T>()` function used everywhere; throws `ApiError` on non-2xx
- **`web/src/types.ts`** — All TypeScript types for API payloads; add new types here
- **`web/src/constants.ts`** — `Role`, `Page`, `TriggerEvent`, `AutomationAction` enums
- **`web/src/hooks/useAsyncData.ts`** — Standard hook for loading data: `useAsyncData(loader, deps, onSuccess, pushNotice, errorTitle)`
- **`web/src/hooks/useFormSubmit.ts`** — Standard hook for form submissions with loading state
- **`web/src/pages/`** — One file per page; receive `{ apiBaseUrl, accessToken, branchId, pushNotice }` as props
- **`web/src/components/`** — Shared UI: `Sidebar`, `NoticeStack` (toast system), `Skeleton`, `QrScannerModal`

Notifications/toasts flow through `pushNotice(tone, title, detail)` passed down as a prop to all pages.

## Testing

Tests use SQLite in-memory via pytest fixtures in `tests/conftest.py`. Fixtures provide a sample org, branch, user, and staff record for common setup. Do not mock the database — tests hit a real (SQLite) session.

## Environment

Backend config is in `.env` (copy from `.env.example`). Settings are loaded via `pydantic-settings` in `app/config.py`. The app runs on `http://localhost:8000`; frontend dev proxy targets `http://127.0.0.1:8000`.
