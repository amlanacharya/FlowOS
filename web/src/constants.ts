export const Role = {
  Owner: 'owner',
  BranchManager: 'branch_manager',
  FrontDesk: 'front_desk',
  Trainer: 'trainer',
  Member: 'member',
} as const

export type RoleValue = (typeof Role)[keyof typeof Role]

export const Page = {
  Dashboard: 'dashboard',
  Leads: 'leads',
  Members: 'members',
  Payments: 'payments',
  StaffAttendance: 'staff-attendance',
  Engagement: 'engagement',
  Trainer: 'trainer',
  Reports: 'reports',
  Automation: 'automation',
  Settings: 'settings',
} as const

export type PageValue = (typeof Page)[keyof typeof Page]

export const MANAGER_ROLES = [Role.Owner, Role.BranchManager] as const
export const TRAINER_ALLOWED_PAGES = [Page.Trainer, Page.Engagement, Page.Settings] as const

export const TriggerEvent = {
  SubscriptionExpiring: 'subscription_expiring',
  LeadStale: 'lead_stale',
  DuesOverdue: 'dues_overdue',
} as const

export type TriggerEventValue = (typeof TriggerEvent)[keyof typeof TriggerEvent]

export const AutomationAction = {
  SendWhatsApp: 'send_whatsapp',
  AlertManager: 'alert_manager',
} as const

export type AutomationActionValue = (typeof AutomationAction)[keyof typeof AutomationAction]

export const TRIGGER_EVENT_LABELS: Record<TriggerEventValue, string> = {
  [TriggerEvent.SubscriptionExpiring]: 'Subscription expiring',
  [TriggerEvent.LeadStale]: 'Lead stale',
  [TriggerEvent.DuesOverdue]: 'Dues overdue',
}

export const ACTION_LABELS: Record<AutomationActionValue, string> = {
  [AutomationAction.SendWhatsApp]: 'Send WhatsApp',
  [AutomationAction.AlertManager]: 'Alert manager',
}
