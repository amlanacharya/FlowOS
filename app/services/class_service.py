from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import ClassEnrollment, ClassSession
from app.schemas.class_session import ClassSessionCreate


class ClassService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, branch_id: UUID, data: ClassSessionCreate) -> ClassSession:
        """Create a new class session."""
        session = ClassSession(branch_id=branch_id, **data.dict())
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get_session(self, session_id: UUID) -> Optional[ClassSession]:
        """Retrieve a class session by ID."""
        return await self.session.get(ClassSession, session_id)

    async def list_sessions(self, branch_id: UUID, skip: int = 0, limit: int = 100) -> List[ClassSession]:
        """List all active class sessions for a branch."""
        statement = (
            select(ClassSession)
            .where(ClassSession.branch_id == branch_id)
            .where(ClassSession.is_cancelled == False)
            .order_by(ClassSession.scheduled_at)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def enroll_member(self, session_id: UUID, member_id: UUID, branch_id: UUID) -> Optional[ClassEnrollment]:
        """Enroll a member in a class session."""
        session = await self.get_session(session_id)
        if not session:
            return None
        if session.enrolled_count >= session.capacity:
            raise ValueError("Class is at capacity")

        # Check for existing enrollment
        statement = (
            select(ClassEnrollment)
            .where(ClassEnrollment.session_id == session_id)
            .where(ClassEnrollment.member_id == member_id)
        )
        result = await self.session.execute(statement)
        existing = result.scalars().first()
        if existing:
            raise ValueError("Member already enrolled")

        enrollment = ClassEnrollment(
            session_id=session_id,
            member_id=member_id,
            branch_id=branch_id,
        )
        session.enrolled_count += 1
        self.session.add(enrollment)
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(enrollment)
        return enrollment

    async def cancel_enrollment(self, enrollment_id: UUID) -> bool:
        """Cancel a class enrollment."""
        enrollment = await self.session.get(ClassEnrollment, enrollment_id)
        if not enrollment:
            return False
        enrollment.cancelled = True
        session = await self.get_session(enrollment.session_id)
        if session:
            session.enrolled_count = max(0, session.enrolled_count - 1)
            self.session.add(session)
        self.session.add(enrollment)
        await self.session.commit()
        return True

    async def mark_attendance(self, enrollment_id: UUID) -> Optional[ClassEnrollment]:
        """Mark a member as attended for a class session."""
        enrollment = await self.session.get(ClassEnrollment, enrollment_id)
        if not enrollment:
            return None
        enrollment.attended = True
        self.session.add(enrollment)
        await self.session.commit()
        await self.session.refresh(enrollment)
        return enrollment

    async def cancel_session(self, session_id: UUID, reason: Optional[str] = None) -> Optional[ClassSession]:
        """Cancel a class session."""
        session = await self.get_session(session_id)
        if not session:
            return None
        session.is_cancelled = True
        session.cancellation_reason = reason
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session
