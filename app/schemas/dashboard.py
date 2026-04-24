from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlmodel import SQLModel


class DashboardSummary(SQLModel):
    active_members: int
    total_revenue_mtd: float
    leads_this_week: int
    trials_scheduled: int
    trials_converted: int
    renewals_due_7_days: int
    collections_today: float
    outstanding_dues: float
    classes_today: int
    class_fill_rate: float
    inactive_members: int


class RevenueBreakdown(SQLModel):
    date: date
    amount: Decimal
    count: int


class DuesReport(SQLModel):
    member_id: UUID
    full_name: str
    amount_due: float
    days_overdue: int


class LeadFunnel(SQLModel):
    new: int
    contacted: int
    trial_scheduled: int
    trial_attended: int
    converted: int
    lost: int


class AttendanceTrend(SQLModel):
    date: date
    checkin_count: int
    checkout_count: int
