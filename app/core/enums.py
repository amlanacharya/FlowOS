from enum import Enum


class RoleEnum(str, Enum):
    OWNER = "owner"
    BRANCH_MANAGER = "branch_manager"
    FRONT_DESK = "front_desk"
    TRAINER = "trainer"
    MEMBER = "member"


class LeadStatusEnum(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    TRIAL_SCHEDULED = "trial_scheduled"
    TRIAL_ATTENDED = "trial_attended"
    CONVERTED = "converted"
    LOST = "lost"


class MemberStatusEnum(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PAUSED = "paused"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    BLACKLISTED = "blacklisted"


class SubscriptionStatusEnum(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PAUSED = "paused"


class PlanTypeEnum(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half_yearly"
    ANNUALLY = "annually"
    LIFETIME = "lifetime"


class InvoiceStatusEnum(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class InvoiceTypeEnum(str, Enum):
    NEW_JOIN = "new_join"
    RENEWAL = "renewal"
    ADDON = "addon"
    ADJUSTMENT = "adjustment"


class ShiftTypeEnum(str, Enum):
    REGULAR = "regular"
    OVERTIME = "overtime"
    TRAINING = "training"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class PaymentModeEnum(str, Enum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"


class AttendanceTypeEnum(str, Enum):
    GYM_CHECKIN = "gym_checkin"
    CLASS_ATTENDANCE = "class_attendance"
    TRIAL_ATTENDANCE = "trial_attendance"
