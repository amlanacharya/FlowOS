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
  source?: string
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

export type QrCheckinResponse = {
  attendance_id: string
  member_id: string
  member_name: string
  subscription_end_date: string | null
  amount_due: number
  checked_in_at: string
}

export type StaffAttendance = {
  id: string
  staff_id: string
  branch_id: string
  checked_in_at: string
  checked_out_at: string | null
  attendance_date: string
  notes: string | null
}

export type StaffAttendanceList = {
  items: StaffAttendance[]
  total: number
}

export type StaffShift = {
  id: string
  branch_id: string
  staff_id: string
  shift_date: string
  shift_start: string
  shift_end: string
  shift_type: string
  notes: string | null
  created_at: string
}

export type StaffShiftCreate = {
  shift_date: string
  shift_start: string
  shift_end: string
  shift_type?: string
  notes?: string
}

export type ShiftComparison = {
  staff_id: string
  scheduled_hours: number
  actual_hours: number
  difference: number
  attendance_count: number
}

export type WorkoutLog = {
  id: string
  member_id: string
  branch_id: string
  workout_date: string
  exercise_name: string
  sets: number | null
  reps: number | null
  weight_kg: number | null
  notes: string | null
  logged_by_staff_id: string | null
  created_at: string
}

export type WorkoutLogCreate = {
  member_id: string
  date?: string
  exercise_name: string
  sets?: number
  reps?: number
  weight_kg?: number
  notes?: string
}

export type MemberFeedback = {
  id: string
  member_id: string
  branch_id: string
  rating: number
  comment: string | null
  submitted_at: string
}

export type FeedbackSummary = {
  average_rating: number
  total: number
  recent: MemberFeedback[]
}

export type TrainerEnrollmentMember = {
  enrollment_id: string
  member_id: string
  member_name: string
  attended: boolean
  cancelled: boolean
}

export type TrainerSession = {
  session_id: string
  class_type_id: string
  scheduled_at: string
  duration_minutes: number
  capacity: number
  enrolled_count: number
  members: TrainerEnrollmentMember[]
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
