from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import Branch, Lead, Organization
from app.schemas.public import PublicLeadCreate, PublicLeadResponse

router = APIRouter(prefix="/api/v1/public", tags=["public"])


async def resolve_branch(session: AsyncSession, branch_slug: str) -> Branch:
    result = await session.execute(
        select(Branch)
        .join(Organization, Organization.id == Branch.organization_id)
        .where(Organization.slug == branch_slug, Branch.is_active == True)
        .order_by(Branch.created_at)
    )
    branch = result.scalars().first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch


@router.post("/leads", response_model=PublicLeadResponse)
async def public_lead(data: PublicLeadCreate, session: AsyncSession = Depends(get_session)) -> PublicLeadResponse:
    branch = await resolve_branch(session, data.branch_slug)
    lead = Lead(
        branch_id=branch.id,
        full_name=data.full_name,
        phone=data.phone,
        email=data.email,
        source=data.source,
        notes=data.notes,
        utm_source=data.utm_source,
        utm_medium=data.utm_medium,
        utm_campaign=data.utm_campaign,
    )
    session.add(lead)
    await session.commit()
    await session.refresh(lead)
    return PublicLeadResponse(id=lead.id, message="We'll be in touch soon!")


@router.get("/embed/{branch_slug}", response_class=HTMLResponse)
async def embed_form(branch_slug: str) -> HTMLResponse:
    html = f"""
    <form method="post" action="/api/v1/public/leads">
      <input type="hidden" name="branch_slug" value="{branch_slug}" />
      <input name="full_name" placeholder="Full name" required />
      <input name="phone" placeholder="Phone" required />
      <input name="email" placeholder="Email" />
      <button type="submit">Request a callback</button>
    </form>
    """
    return HTMLResponse(html)
