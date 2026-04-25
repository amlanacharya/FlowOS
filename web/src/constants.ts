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
