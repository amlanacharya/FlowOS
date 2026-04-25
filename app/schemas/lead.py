from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import LeadStatusEnum


class LeadCreate(SQLModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    source: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdate(SQLModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(SQLModel):
    id: UUID
    branch_id: UUID
    full_name: str
    phone: str
    source: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    status: LeadStatusEnum
    trial_scheduled_at: Optional[datetime]
    created_at: datetime


class CampaignAnalytics(SQLModel):
    utm_campaign: str
    total_leads: int
    converted: int
    conversion_rate: float
