#!/usr/bin/env python3
"""Quick sanity check that all modules import correctly."""
import sys
import importlib

MODULES_TO_CHECK = [
    # Core
    ("app.core.enums", ["RoleEnum", "LeadStatusEnum", "MemberStatusEnum"]),
    ("app.core.security", ["hash_password", "verify_password", "create_access_token"]),
    ("app.core.exceptions", ["InvalidCredentialsException"]),
    ("app.config", ["Settings"]),
    ("app.database", ["get_session"]),
    ("app.deps", ["require_roles", "get_branch_scope"]),

    # Models
    ("app.models", ["Organization", "Branch", "User", "Staff", "Lead", "Member", "Payment", "Attendance"]),

    # Schemas
    ("app.schemas", ["LoginRequest", "TokenResponse", "OrganizationCreate"]),

    # Routers
    ("app.routers.auth", ["router"]),
    ("app.routers.organizations", ["router"]),
    ("app.routers.branches", ["router"]),
    ("app.routers.staff", ["router"]),
    ("app.routers.leads", ["router"]),
    ("app.routers.members", ["router"]),
    ("app.routers.plans", ["router"]),
    ("app.routers.subscriptions", ["router"]),
    ("app.routers.payments", ["router"]),
    ("app.routers.sessions", ["router"]),
    ("app.routers.attendance", ["router"]),
    ("app.routers.dashboard", ["router"]),
    ("app.routers.notifications", ["router"]),

    # Services
    ("app.services.auth_service", ["AuthService"]),
    ("app.services.lead_service", ["LeadService"]),
    ("app.services.member_service", ["MemberService"]),
    ("app.services.payment_service", ["PaymentService"]),
    ("app.services.class_service", ["ClassService"]),
    ("app.services.attendance_service", ["AttendanceService"]),
    ("app.services.dashboard_service", ["DashboardService"]),
    ("app.services.notification_service", ["NotificationService"]),

    # App
    ("app.main", ["app"]),
]

def check_imports():
    """Verify all modules import without error."""
    failed = []
    for module_name, items in MODULES_TO_CHECK:
        try:
            mod = importlib.import_module(module_name)
            for item in items:
                if not hasattr(mod, item):
                    failed.append(f"  ✗ {module_name}: missing '{item}'")
                else:
                    print(f"  ✓ {module_name}.{item}")
        except ImportError as e:
            failed.append(f"  ✗ {module_name}: {e}")

    return failed

if __name__ == "__main__":
    print("🔍 Verifying FlowOS backend build...\n")

    failures = check_imports()

    if not failures:
        print("\n✅ All imports successful!")
        print("\nNext steps:")
        print("  1. docker-compose up")
        print("  2. alembic upgrade head")
        print("  3. Visit http://localhost:8000/docs")
        sys.exit(0)
    else:
        print("\n❌ Build verification failed:")
        for msg in failures:
            print(msg)
        sys.exit(1)
