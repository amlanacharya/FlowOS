# FlowOS Web

A React + Vite frontend for the FlowOS FastAPI backend. The first pass is a single-screen operations console with:

- backend health and auth connection controls
- live pulls from `/api/v1/auth/me`, `/api/v1/dashboard/*`, `/api/v1/leads`, `/api/v1/members`, and `/api/v1/payments/summary`
- direct mutation forms for organization, branch, lead, and member creation
- a distinct visual system instead of the default Vite starter

## Run

```bash
npm install
npm run dev
```

The app defaults to `http://localhost:8000` for the backend. You can override that in the UI or by creating `.env` from `.env.example`:

```bash
cp .env.example .env
```

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Build

```bash
npm run build
```
