from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routers import (
    attendance,
    auth,
    branches,
    class_types,
    dashboard,
    leads,
    members,
    notifications,
    organizations,
    payments,
    plans,
    sessions,
    staff,
    subscriptions,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan: startup and shutdown events.
    """
    # Startup
    await create_tables()
    yield
    # Shutdown


app = FastAPI(
    title="FlowOS Gym Management API",
    version="1.0.0",
    description="Complete gym management system API",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# Mount routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(organizations.router, tags=["Organizations"])
app.include_router(branches.router, tags=["Branches"])
app.include_router(staff.router, tags=["Staff"])
app.include_router(leads.router, tags=["Leads"])
app.include_router(members.router, tags=["Members"])
app.include_router(plans.router, tags=["Plans"])
app.include_router(subscriptions.router, tags=["Subscriptions"])
app.include_router(payments.router, tags=["Payments"])
app.include_router(sessions.router, tags=["Sessions"])
app.include_router(class_types.router, tags=["Class Types"])
app.include_router(attendance.router, tags=["Attendance"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(notifications.router, tags=["Notifications"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
