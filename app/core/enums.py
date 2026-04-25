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


class SubscriptionStatusEnum(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"


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


class TriggerEventEnum(str, Enum):
    SUBSCRIPTION_EXPIRING = "subscription_expiring"
    LEAD_STALE = "lead_stale"
    DUES_OVERDUE = "dues_overdue"


class ActionTypeEnum(str, Enum):
    SEND_WHATSAPP = "send_whatsapp"
    ALERT_MANAGER = "alert_manager"
