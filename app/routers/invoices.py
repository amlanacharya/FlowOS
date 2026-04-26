from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InvoiceStatusEnum, RoleEnum
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.schemas.invoice import InvoiceResponse
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


@router.get("", response_model=List[InvoiceResponse])
async def list_invoices(
    member_id: Optional[UUID] = None,
    invoice_no: Optional[str] = None,
    status: Optional[InvoiceStatusEnum] = None,
    only_outstanding: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(
        require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)
    ),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[InvoiceResponse]:
    service = InvoiceService(session)
    return await service.list_invoices(
        branch_id=branch_id,
        member_id=member_id,
        invoice_no=invoice_no,
        status=status,
        only_outstanding=only_outstanding,
        skip=skip,
        limit=limit,
    )
