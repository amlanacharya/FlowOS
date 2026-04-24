from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import require_roles
from app.models import Organization
from app.schemas.organization import OrganizationCreate, OrganizationResponse

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    org: OrganizationCreate, session: AsyncSession = Depends(get_session)
) -> OrganizationResponse:
    db_org = Organization(**org.dict())
    session.add(db_org)
    await session.commit()
    await session.refresh(db_org)
    return db_org


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> OrganizationResponse:
    org = await session.get(Organization, org_id)
    if not org:
        raise ResourceNotFoundException()
    return org


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    org_update: OrganizationCreate,
    claims: dict = Depends(require_roles(RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> OrganizationResponse:
    org = await session.get(Organization, org_id)
    if not org:
        raise ResourceNotFoundException()
    org.name = org_update.name
    org.slug = org_update.slug
    org.owner_email = org_update.owner_email
    org.phone = org_update.phone
    org.updated_at = datetime.utcnow()
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org
