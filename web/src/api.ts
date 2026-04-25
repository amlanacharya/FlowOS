import type {
  FeedbackSummary,
  MemberFeedback,
  QrCheckinResponse,
  ShiftComparison,
  StaffAttendance,
  StaffAttendanceList,
  StaffShift,
  StaffShiftCreate,
  TrainerEnrollmentMember,
  TrainerSession,
  WorkoutLog,
  WorkoutLogCreate,
} from './types'

type Primitive = string | number | boolean

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  token?: string
  body?: unknown
  query?: Record<string, Primitive | null | undefined>
}

export class ApiError extends Error {
  status: number
  detail: string
  payload: unknown

  constructor(status: number, detail: string, payload: unknown) {
    super(detail)
    this.status = status
    this.detail = detail
    this.payload = payload
  }
}

function buildUrl(
  baseUrl: string,
  path: string,
  query?: Record<string, Primitive | null | undefined>,
): URL {
  const normalizedBase = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`
  const normalizedPath = path.startsWith('/') ? path.slice(1) : path
  const url = new URL(normalizedPath, normalizedBase)

  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }

    url.searchParams.set(key, String(value))
  })

  return url
}

async function parsePayload(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) {
    return null
  }

  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export async function apiFetch<T>(
  baseUrl: string,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const url = buildUrl(baseUrl, path, options.query)
  const headers = new Headers({ Accept: 'application/json' })

  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  if (options.token) {
    headers.set('Authorization', `Bearer ${options.token}`)
  }

  const response = await fetch(url, {
    method: options.method ?? 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  const payload = await parsePayload(response)

  if (!response.ok) {
    const detail =
      typeof payload === 'object' &&
      payload !== null &&
      'detail' in payload &&
      typeof payload.detail === 'string'
        ? payload.detail
        : `Request failed with ${response.status}`

    throw new ApiError(response.status, detail, payload)
  }

  return payload as T
}

// Attendance endpoints
export async function qrCheckin(
  base: string,
  token: string,
  branchId: string,
  memberCode: string,
  notes?: string,
): Promise<QrCheckinResponse> {
  // POST /api/v1/attendance/qr-checkin
  return apiFetch(base, '/api/v1/attendance/qr-checkin', {
    method: 'POST',
    token,
    body: { member_code: memberCode, notes },
    query: { branch_id: branchId },
  })
}

export async function staffCheckin(
  base: string,
  token: string,
  branchId: string,
  notes?: string,
): Promise<StaffAttendance> {
  return apiFetch(base, '/api/v1/staff/checkin', {
    method: 'POST',
    token,
    body: { notes },
    query: { branch_id: branchId },
  })
}

export async function staffCheckout(
  base: string,
  token: string,
  notes?: string,
): Promise<StaffAttendance> {
  return apiFetch(base, '/api/v1/staff/checkout', {
    method: 'POST',
    token,
    body: { notes },
  })
}

export async function listStaffAttendance(
  base: string,
  token: string,
  branchId: string,
  params: { staff_id?: string; date_from?: string; date_to?: string } = {},
): Promise<StaffAttendanceList> {
  return apiFetch(base, '/api/v1/staff/attendance', {
    token,
    query: { branch_id: branchId, ...params },
  })
}

export async function listStaffShifts(
  base: string,
  token: string,
  branchId: string,
  params: { staff_id?: string; date_from?: string; date_to?: string } = {},
): Promise<{ items: StaffShift[]; total: number }> {
  return apiFetch(base, '/api/v1/staff/shifts', {
    token,
    query: { branch_id: branchId, ...params },
  })
}

export async function createStaffShift(
  base: string,
  token: string,
  branchId: string,
  staffId: string,
  shift: StaffShiftCreate,
): Promise<StaffShift> {
  return apiFetch(base, '/api/v1/staff/shifts', {
    method: 'POST',
    token,
    query: { branch_id: branchId, staff_id: staffId },
    body: shift,
  })
}

export async function compareStaffShifts(
  base: string,
  token: string,
  branchId: string,
  staffId: string,
  params: { date_from?: string; date_to?: string } = {},
): Promise<ShiftComparison> {
  return apiFetch(base, `/api/v1/staff/shifts/${staffId}/comparison`, {
    token,
    query: { branch_id: branchId, ...params },
  })
}

export async function createWorkout(
  base: string,
  token: string,
  branchId: string,
  workout: WorkoutLogCreate,
): Promise<WorkoutLog> {
  return apiFetch(base, '/api/v1/workouts', {
    method: 'POST',
    token,
    query: { branch_id: branchId },
    body: workout,
  })
}

export async function listWorkouts(
  base: string,
  token: string,
  branchId: string,
  memberId: string,
): Promise<WorkoutLog[]> {
  return apiFetch(base, `/api/v1/workouts/${memberId}`, {
    token,
    query: { branch_id: branchId },
  })
}

export async function listFeedback(
  base: string,
  token: string,
  branchId: string,
): Promise<MemberFeedback[]> {
  return apiFetch(base, '/api/v1/feedback', {
    token,
    query: { branch_id: branchId },
  })
}

export async function feedbackSummary(
  base: string,
  token: string,
  branchId: string,
): Promise<FeedbackSummary> {
  return apiFetch(base, '/api/v1/feedback/summary', {
    token,
    query: { branch_id: branchId },
  })
}

export async function trainerToday(
  base: string,
  token: string,
  branchId: string,
): Promise<TrainerSession[]> {
  return apiFetch(base, '/api/v1/trainer/today', {
    token,
    query: { branch_id: branchId },
  })
}

export async function markTrainerAttendance(
  base: string,
  token: string,
  branchId: string,
  enrollmentId: string,
  attended: boolean,
): Promise<TrainerEnrollmentMember> {
  return apiFetch(base, `/api/v1/trainer/enrollments/${enrollmentId}/attendance`, {
    method: 'POST',
    token,
    query: { branch_id: branchId, attended },
  })
}
