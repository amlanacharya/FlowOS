from datetime import date
from decimal import Decimal
from typing import Dict, List
from uuid import UUID

from sqlmodel import SQLModel


class DailySalesReport(SQLModel):
    date: date
    total_collection: Decimal
    collection_by_mode: Dict[str, Decimal]
    new_members: int
    renewals: int
    leads_converted: int


class AtRiskMember(SQLModel):
    member_id: UUID
    full_name: str
    expiry_date: date
    days_since_expiry: int


class RetentionReport(SQLModel):
    total_expired: int
    not_renewed_within_30d: int
    churn_rate: float
    at_risk_members: List[AtRiskMember]


class TrainerPerformanceRow(SQLModel):
    staff_id: UUID
    trainer_name: str
    sessions_delivered: int
    avg_fill_rate: float
    total_member_hours: float


class RevenueWindow(SQLModel):
    count: int
    projected_amount: Decimal


class RevenueForecast(SQLModel):
    next_30_days: RevenueWindow
    next_60_days: RevenueWindow
    next_90_days: RevenueWindow


class PeakHourBucket(SQLModel):
    hour: int
    checkin_count: int


class MonthlyRevenue(SQLModel):
    month: str
    total_revenue: Decimal
    payment_count: int
