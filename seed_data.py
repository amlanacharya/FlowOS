#!/usr/bin/env python3
"""
Seed FlowOS database with sample data for development.
Run after: alembic upgrade head
"""
from sqlmodel import Session, create_engine
from sqlmodel import SQLModel
from datetime import date, datetime, timedelta
from decimal import Decimal
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.models import (
    Organization, Branch, User, Staff, Lead, Member,
    MembershipPlan, MemberSubscription, Payment, ClassType,
    ClassSession, Attendance
)
from app.core.enums import (
    RoleEnum, LeadStatusEnum, MemberStatusEnum,
    SubscriptionStatusEnum, PaymentModeEnum, AttendanceTypeEnum
)
from app.core.security import hash_password
from app.config import Settings

settings = Settings()

def seed_database():
    """Populate database with sample data."""
    engine = create_engine(
        settings.database_url,
        echo=True,
    )

    # Create tables if not exist
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Clear existing data (for development only!)
        # Commented out to be safe
        # for model in [Attendance, ClassSession, ClassType, Payment, MemberSubscription,
        #              MembershipPlan, Member, Lead, Staff, User, Branch, Organization]:
        #     for item in session.query(model).all():
        #         session.delete(item)
        # session.commit()

        print("🌱 Seeding sample data...\n")

        # 1. Organization
        org = Organization(
            name="FitLife Gym",
            slug="fitlife-gym",
            owner_email="owner@fitlife.com",
            phone="+1234567890",
        )
        session.add(org)
        session.flush()
        print(f"✓ Created organization: {org.name} (id: {org.id})")

        # 2. Branch
        branch = Branch(
            organization_id=org.id,
            name="Main Branch - Downtown",
            address="123 Fitness Street",
            city="New York",
            phone="+1234567890",
        )
        session.add(branch)
        session.flush()
        print(f"✓ Created branch: {branch.name}")

        # 3. Users & Staff
        owner_user = User(
            email="owner@fitlife.com",
            hashed_password=hash_password("OwnerPass123!"),
            full_name="John Owner",
            is_verified=True,
        )
        session.add(owner_user)
        session.flush()

        owner_staff = Staff(
            user_id=owner_user.id,
            organization_id=org.id,
            branch_id=branch.id,
            role=RoleEnum.owner,
            joined_at=date.today(),
        )
        session.add(owner_staff)
        session.flush()
        print(f"✓ Created owner: {owner_user.full_name}")

        manager_user = User(
            email="manager@fitlife.com",
            hashed_password=hash_password("ManagerPass123!"),
            full_name="Sarah Manager",
            is_verified=True,
        )
        session.add(manager_user)
        session.flush()

        manager_staff = Staff(
            user_id=manager_user.id,
            organization_id=org.id,
            branch_id=branch.id,
            role=RoleEnum.branch_manager,
            joined_at=date.today(),
        )
        session.add(manager_staff)
        session.flush()
        print(f"✓ Created manager: {manager_user.full_name}")

        trainer_user = User(
            email="trainer@fitlife.com",
            hashed_password=hash_password("TrainerPass123!"),
            full_name="Mike Trainer",
            is_verified=True,
        )
        session.add(trainer_user)
        session.flush()

        trainer_staff = Staff(
            user_id=trainer_user.id,
            organization_id=org.id,
            branch_id=branch.id,
            role=RoleEnum.trainer,
            specialization="CrossFit",
            joined_at=date.today(),
        )
        session.add(trainer_staff)
        session.flush()
        print(f"✓ Created trainer: {trainer_user.full_name}")

        # 4. Membership Plans
        monthly_plan = MembershipPlan(
            branch_id=branch.id,
            name="Monthly Pro",
            duration_days=30,
            price=Decimal("49.99"),
            includes_classes=True,
            max_class_sessions=16,
        )
        session.add(monthly_plan)
        session.flush()

        quarterly_plan = MembershipPlan(
            branch_id=branch.id,
            name="Quarterly Plus",
            duration_days=90,
            price=Decimal("129.99"),
            includes_classes=True,
            max_class_sessions=50,
            max_freezes_allowed=2,
        )
        session.add(quarterly_plan)
        session.flush()
        print(f"✓ Created {2} membership plans")

        # 5. Leads
        leads_data = [
            ("Alice Smith", "+1111111111", LeadStatusEnum.new),
            ("Bob Johnson", "+2222222222", LeadStatusEnum.contacted),
            ("Carol White", "+3333333333", LeadStatusEnum.trial_scheduled),
        ]
        leads = []
        for name, phone, status in leads_data:
            lead = Lead(
                branch_id=branch.id,
                full_name=name,
                phone=phone,
                status=status,
                assigned_to_staff_id=manager_staff.id,
            )
            session.add(lead)
            leads.append(lead)
        session.flush()
        print(f"✓ Created {len(leads)} leads")

        # 6. Members
        members_data = [
            ("David Brown", "+4444444444"),
            ("Emma Davis", "+5555555555"),
            ("Frank Miller", "+6666666666"),
        ]
        members = []
        for i, (name, phone) in enumerate(members_data):
            member = Member(
                branch_id=branch.id,
                full_name=name,
                phone=phone,
                member_code=f"BR01-{1001+i:04d}",
                status=MemberStatusEnum.active,
                joined_at=date.today() - timedelta(days=30*i),
            )
            session.add(member)
            members.append(member)
        session.flush()
        print(f"✓ Created {len(members)} members")

        # 7. Subscriptions
        for i, member in enumerate(members):
            start_date = date.today() - timedelta(days=15+i*5)
            end_date = start_date + timedelta(days=30)
            sub = MemberSubscription(
                member_id=member.id,
                branch_id=branch.id,
                plan_id=monthly_plan.id,
                start_date=start_date,
                end_date=end_date,
                status=SubscriptionStatusEnum.active,
                total_amount=monthly_plan.price,
                amount_paid=Decimal("49.99") if i > 0 else Decimal("0.00"),
                amount_due=Decimal("0.00") if i > 0 else monthly_plan.price,
                created_by_staff_id=manager_staff.id,
            )
            session.add(sub)
        session.flush()
        print(f"✓ Created subscriptions for {len(members)} members")

        # 8. Payments
        for i, member in enumerate(members[1:], 1):
            payment = Payment(
                branch_id=branch.id,
                member_id=member.id,
                subscription_id=None,  # Would normally reference subscription
                amount=Decimal("49.99"),
                mode=PaymentModeEnum.cash if i % 2 == 0 else PaymentModeEnum.card,
                received_by_staff_id=manager_staff.id,
                payment_date=date.today() - timedelta(days=i*5),
            )
            session.add(payment)
        session.flush()
        print(f"✓ Created payments")

        # 9. Class Types
        class_types = []
        for name in ["Yoga", "CrossFit", "Zumba", "Boxing"]:
            ct = ClassType(
                branch_id=branch.id,
                name=name,
                duration_minutes=60,
            )
            session.add(ct)
            class_types.append(ct)
        session.flush()
        print(f"✓ Created {len(class_types)} class types")

        # 10. Class Sessions
        for i in range(3):
            session_time = datetime.now() + timedelta(days=i, hours=9)
            cs = ClassSession(
                branch_id=branch.id,
                class_type_id=class_types[i % len(class_types)].id,
                trainer_staff_id=trainer_staff.id,
                scheduled_at=session_time,
                capacity=20,
                enrolled_count=min(i*3, 15),
            )
            session.add(cs)
        session.flush()
        print(f"✓ Created class sessions")

        # 11. Attendance
        for i, member in enumerate(members):
            checkin_time = datetime.now() - timedelta(days=i, hours=1)
            att = Attendance(
                branch_id=branch.id,
                member_id=member.id,
                attendance_type=AttendanceTypeEnum.gym_checkin,
                checked_in_at=checkin_time,
                checked_out_at=checkin_time + timedelta(hours=1, minutes=15),
                recorded_by_staff_id=manager_staff.id,
            )
            session.add(att)
        session.flush()
        print(f"✓ Created attendance records")

        # Commit all changes
        session.commit()
        print("\n✅ Sample data seeding complete!\n")

        print("Test Credentials:")
        print(f"  Email: owner@fitlife.com")
        print(f"  Password: OwnerPass123!")
        print(f"\nNext: Visit http://localhost:8000/docs and test login")

if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        sys.exit(1)
