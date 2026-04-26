from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import InvoiceStatusEnum, InvoiceTypeEnum, PlanTypeEnum
from app.models import Invoice, MembershipPlan


class InvoiceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_invoice_no(self, branch_id: UUID) -> str:
        statement = (
            select(Invoice)
            .where(Invoice.branch_id == branch_id)
            .order_by(Invoice.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(statement)
        last = result.scalars().first()
        prefix = f"INV-{branch_id.hex[:6].upper()}"
        sequence = 1001

        if last:
            parts = last.invoice_no.split("-")
            if len(parts) >= 3:
                try:
                    sequence = int(parts[-1]) + 1
                except ValueError:
                    pass

        return f"{prefix}-{sequence:04d}"

    async def create_invoice(
        self,
        branch_id: UUID,
        member_id: UUID,
        subscription_id: Optional[UUID],
        created_by_staff_id: UUID,
        subtotal: Decimal,
        invoice_type: InvoiceTypeEnum,
        due_date: Optional[date] = None,
        registration_fee: Decimal = Decimal("0.00"),
        discount: Decimal = Decimal("0.00"),
        tax: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
    ) -> Invoice:
        total = subtotal + registration_fee + tax - discount
        total = max(total, Decimal("0.00"))
        invoice = Invoice(
            invoice_no=await self.generate_invoice_no(branch_id),
            branch_id=branch_id,
            member_id=member_id,
            subscription_id=subscription_id,
            invoice_type=invoice_type,
            status=InvoiceStatusEnum.ISSUED,
            subtotal=subtotal,
            registration_fee=registration_fee,
            discount=discount,
            tax=tax,
            total_amount=total,
            amount_due=total,
            due_date=due_date or date.today(),
            notes=notes,
            created_by_staff_id=created_by_staff_id,
        )
        self.session.add(invoice)
        await self.session.flush()
        return invoice

    async def create_subscription_invoice(
        self,
        branch_id: UUID,
        member_id: UUID,
        subscription_id: UUID,
        plan: MembershipPlan,
        created_by_staff_id: UUID,
        invoice_type: InvoiceTypeEnum,
    ) -> Invoice:
        registration_fee = Decimal("0.00")
        if invoice_type == InvoiceTypeEnum.NEW_JOIN and plan.plan_type == PlanTypeEnum.MONTHLY:
            registration_fee = plan.registration_fee

        return await self.create_invoice(
            branch_id=branch_id,
            member_id=member_id,
            subscription_id=subscription_id,
            created_by_staff_id=created_by_staff_id,
            subtotal=plan.price,
            registration_fee=registration_fee,
            invoice_type=invoice_type,
        )

    async def get_invoice(self, invoice_id: UUID) -> Optional[Invoice]:
        return await self.session.get(Invoice, invoice_id)

    async def list_invoices(
        self,
        branch_id: UUID,
        member_id: Optional[UUID] = None,
        invoice_no: Optional[str] = None,
        status: Optional[InvoiceStatusEnum] = None,
        only_outstanding: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Invoice]:
        query = select(Invoice).where(Invoice.branch_id == branch_id)
        if member_id:
            query = query.where(Invoice.member_id == member_id)
        if invoice_no:
            query = query.where(Invoice.invoice_no == invoice_no)
        if status:
            query = query.where(Invoice.status == status)
        if only_outstanding:
            query = query.where(Invoice.amount_due > 0)

        result = await self.session.execute(
            query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def apply_payment(self, invoice: Invoice, amount: Decimal) -> None:
        updated_paid = invoice.amount_paid + amount
        invoice.amount_paid = min(invoice.total_amount, updated_paid)
        invoice.amount_due = max(Decimal("0.00"), invoice.total_amount - updated_paid)
        if invoice.amount_due == Decimal("0.00"):
            invoice.status = InvoiceStatusEnum.PAID
        elif invoice.amount_paid > Decimal("0.00"):
            invoice.status = InvoiceStatusEnum.PARTIAL
        invoice.updated_at = datetime.utcnow()
        self.session.add(invoice)
