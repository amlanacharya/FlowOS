"""Router modules for API endpoints."""
from . import (
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

__all__ = [
    "auth",
    "organizations",
    "branches",
    "staff",
    "leads",
    "members",
    "plans",
    "subscriptions",
    "payments",
    "sessions",
    "class_types",
    "attendance",
    "dashboard",
    "notifications",
]
