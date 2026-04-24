export type HealthPayload = {
  status: string
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type UserProfile = {
  id: string
  email: string
  full_name: string
  role: string
  branch_id: string
  org_id: string
  staff_id: string
}

export type DashboardSummary = {
  active_members: number
  total_revenue_mtd: number
  leads_this_week: number
  trials_scheduled: number
  trials_converted: number
  renewals_due_7_days: number
  collections_today: number
  outstanding_dues: number
  classes_today: number
  class_fill_rate: number
  inactive_members: number
}

export type LeadFunnel = {
  new: number
  contacted: number
  trial_scheduled: number
  trial_attended: number
  converted: number
  lost: number
}

export type RevenueBreakdown = {
  date: string
  amount: number
  count: number
}

export type DuesReport = {
  member_id: string
  full_name: string
  amount_due: number
  days_overdue: number
}

export type PaymentSummary = {
  today_collection: number
  outstanding_dues: number
}

export type Lead = {
  id: string
  branch_id: string
  full_name: string
  phone: string
  status: string
  trial_scheduled_at: string | null
  created_at: string
}

export type Member = {
  id: string
  branch_id: string
  full_name: string
  phone: string
  member_code: string
  status: string
  joined_at: string
  created_at: string
}

export type Organization = {
  id: string
  name: string
  slug: string
  owner_email: string
  is_active: boolean
  created_at: string
}

export type Branch = {
  id: string
  organization_id: string
  name: string
  address: string | null
  is_active: boolean
  created_at: string
}

export type OrganizationCreate = {
  name: string
  slug: string
  owner_email: string
  phone?: string
}

export type BranchCreate = {
  name: string
  address?: string
  city?: string
  phone?: string
}

export type LeadCreate = {
  full_name: string
  phone: string
  email?: string
  source?: string
  notes?: string
}

export type MemberCreate = {
  full_name: string
  phone: string
  email?: string
  gender?: string
  emergency_contact?: string
}
