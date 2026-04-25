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
): Promise<any> {
  // POST /api/v1/attendance/qr-checkin
  return apiFetch(base, '/api/v1/attendance/qr-checkin', {
    method: 'POST',
    token,
    body: { member_code: memberCode, notes },
    query: { branch_id: branchId },
  })
}
