import {
  type FormEvent,
  startTransition,
  useEffect,
  useEffectEvent,
  useDeferredValue,
  useState,
} from 'react'
import './App.css'
import { ApiError, apiFetch } from './api'
import type {
  Branch,
  BranchCreate,
  DashboardSummary,
  DuesReport,
  HealthPayload,
  Lead,
  LeadCreate,
  LeadFunnel,
  Member,
  MemberCreate,
  Organization,
  OrganizationCreate,
  PaymentSummary,
  RevenueBreakdown,
  TokenResponse,
  UserProfile,
} from './types'

type Tone = 'success' | 'error' | 'info'

type Notice = {
  id: number
  tone: Tone
  title: string
  detail: string
}

const moduleAtlas = [
  {
    label: 'Acquisition',
    caption: 'Leads, trial scheduling, funnel progression',
    endpoints: ['/api/v1/leads', '/api/v1/dashboard/lead-funnel'],
  },
  {
    label: 'Retention',
    caption: 'Member profiles, pauses, reactivation, dues follow-up',
    endpoints: ['/api/v1/members', '/api/v1/dashboard/dues'],
  },
  {
    label: 'Revenue',
    caption: 'Payments, MTD revenue, collections pulse',
    endpoints: ['/api/v1/payments', '/api/v1/dashboard/revenue'],
  },
  {
    label: 'Operations',
    caption: 'Organizations, branches, staff, role-scoped access',
    endpoints: ['/api/v1/organizations', '/api/v1/branches', '/api/v1/staff'],
  },
  {
    label: 'Programming',
    caption: 'Classes, attendance, fill rate, daily session load',
    endpoints: ['/api/v1/sessions', '/api/v1/attendance', '/api/v1/class-types'],
  },
  {
    label: 'Identity',
    caption: 'JWT login, refresh, self profile, branch-aware permissions',
    endpoints: ['/api/v1/auth/login', '/api/v1/auth/me', '/api/v1/auth/refresh'],
  },
]

const dashboardStatConfig: Array<{
  key: keyof DashboardSummary
  label: string
  accent: string
  formatter?: (value: number) => string
}> = [
  { key: 'active_members', label: 'Active members', accent: 'mint' },
  {
    key: 'total_revenue_mtd',
    label: 'Revenue MTD',
    accent: 'gold',
    formatter: formatCurrency,
  },
  { key: 'leads_this_week', label: 'Leads this week', accent: 'coral' },
  { key: 'classes_today', label: 'Classes today', accent: 'sky' },
  {
    key: 'class_fill_rate',
    label: 'Fill rate',
    accent: 'plum',
    formatter: (value) => `${Math.round(value)}%`,
  },
  {
    key: 'outstanding_dues',
    label: 'Outstanding dues',
    accent: 'ink',
    formatter: formatCurrency,
  },
]

const defaultSummary: DashboardSummary = {
  active_members: 0,
  total_revenue_mtd: 0,
  leads_this_week: 0,
  trials_scheduled: 0,
  trials_converted: 0,
  renewals_due_7_days: 0,
  collections_today: 0,
  outstanding_dues: 0,
  classes_today: 0,
  class_fill_rate: 0,
  inactive_members: 0,
}

const defaultFunnel: LeadFunnel = {
  new: 0,
  contacted: 0,
  trial_scheduled: 0,
  trial_attended: 0,
  converted: 0,
  lost: 0,
}

const defaultOrganizationForm: OrganizationCreate = {
  name: '',
  slug: '',
  owner_email: '',
  phone: '',
}

const defaultBranchForm: BranchCreate & { org_id: string } = {
  org_id: '',
  name: '',
  address: '',
  city: '',
  phone: '',
}

const defaultLeadForm: LeadCreate = {
  full_name: '',
  phone: '',
  email: '',
  source: '',
  notes: '',
}

const defaultMemberForm: MemberCreate = {
  full_name: '',
  phone: '',
  email: '',
  gender: '',
  emergency_contact: '',
}

function readStoredValue(key: string, fallback = ''): string {
  if (typeof window === 'undefined') {
    return fallback
  }

  return window.localStorage.getItem(key) ?? fallback
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatDate(value: string | null): string {
  if (!value) {
    return 'Pending'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('en-IN', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

function formatRole(role: string): string {
  return role.replaceAll('_', ' ')
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.detail
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Unexpected error'
}

function App() {
  const defaultApiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
  const [apiBaseUrl, setApiBaseUrl] = useState(() =>
    readStoredValue('flowos-api-base', defaultApiBase),
  )
  const [accessToken, setAccessToken] = useState(() =>
    readStoredValue('flowos-access-token'),
  )
  const [refreshToken, setRefreshToken] = useState(() =>
    readStoredValue('flowos-refresh-token'),
  )
  const [tokenInput, setTokenInput] = useState(() =>
    readStoredValue('flowos-access-token'),
  )
  const [branchOverride, setBranchOverride] = useState(() =>
    readStoredValue('flowos-branch-override'),
  )
  const [email, setEmail] = useState('owner@gym.com')
  const [password, setPassword] = useState('')
  const [health, setHealth] = useState<'checking' | 'online' | 'offline'>(
    'checking',
  )
  const [healthDetail, setHealthDetail] = useState('Probing backend')
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [summary, setSummary] = useState<DashboardSummary>(defaultSummary)
  const [funnel, setFunnel] = useState<LeadFunnel>(defaultFunnel)
  const [revenue, setRevenue] = useState<RevenueBreakdown[]>([])
  const [dues, setDues] = useState<DuesReport[]>([])
  const [paymentSummary, setPaymentSummary] = useState<PaymentSummary | null>(null)
  const [leads, setLeads] = useState<Lead[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [createdOrganization, setCreatedOrganization] =
    useState<Organization | null>(null)
  const [createdBranch, setCreatedBranch] = useState<Branch | null>(null)
  const [organizationForm, setOrganizationForm] = useState(defaultOrganizationForm)
  const [branchForm, setBranchForm] = useState(defaultBranchForm)
  const [leadForm, setLeadForm] = useState(defaultLeadForm)
  const [memberForm, setMemberForm] = useState(defaultMemberForm)
  const [leadSearch, setLeadSearch] = useState('')
  const [memberSearch, setMemberSearch] = useState('')
  const [authBusy, setAuthBusy] = useState(false)
  const [dataBusy, setDataBusy] = useState(false)
  const [notices, setNotices] = useState<Notice[]>([])

  const deferredLeadSearch = useDeferredValue(leadSearch.trim().toLowerCase())
  const deferredMemberSearch = useDeferredValue(memberSearch.trim().toLowerCase())
  const activeBranchId = branchOverride.trim() || profile?.branch_id || ''
  const liveDataReady = Boolean(accessToken)

  const filteredLeads = leads.filter((lead) => {
    if (!deferredLeadSearch) {
      return true
    }

    return `${lead.full_name} ${lead.phone} ${lead.status}`
      .toLowerCase()
      .includes(deferredLeadSearch)
  })

  const filteredMembers = members.filter((member) => {
    if (!deferredMemberSearch) {
      return true
    }

    return `${member.full_name} ${member.phone} ${member.member_code} ${member.status}`
      .toLowerCase()
      .includes(deferredMemberSearch)
  })

  function pushNotice(tone: Tone, title: string, detail: string) {
    setNotices((current) => [
      { id: Date.now() + Math.random(), tone, title, detail },
      ...current,
    ].slice(0, 4))
  }

  useEffect(() => {
    window.localStorage.setItem('flowos-api-base', apiBaseUrl)
  }, [apiBaseUrl])

  useEffect(() => {
    window.localStorage.setItem('flowos-access-token', accessToken)
  }, [accessToken])

  useEffect(() => {
    window.localStorage.setItem('flowos-refresh-token', refreshToken)
  }, [refreshToken])

  useEffect(() => {
    window.localStorage.setItem('flowos-branch-override', branchOverride)
  }, [branchOverride])

  const refreshHealth = useEffectEvent(async () => {
    setHealth('checking')
    setHealthDetail('Pinging /health')

    try {
      const response = await apiFetch<HealthPayload>(apiBaseUrl, '/health')
      setHealth('online')
      setHealthDetail(`Backend says ${response.status}`)
    } catch (error) {
      setHealth('offline')
      setHealthDetail(errorMessage(error))
    }
  })

  const refreshProfile = useEffectEvent(async (token: string) => {
    try {
      const nextProfile = await apiFetch<UserProfile>(apiBaseUrl, '/api/v1/auth/me', {
        token,
      })
      setProfile(nextProfile)
    } catch (error) {
      setProfile(null)
      pushNotice('error', 'Profile sync failed', errorMessage(error))
    }
  })

  const refreshLiveData = useEffectEvent(async () => {
    if (!accessToken) {
      setSummary(defaultSummary)
      setFunnel(defaultFunnel)
      setRevenue([])
      setDues([])
      setPaymentSummary(null)
      setLeads([])
      setMembers([])
      return
    }

    setDataBusy(true)
    const query = activeBranchId ? { branch_id: activeBranchId } : undefined

    const [
      summaryResult,
      funnelResult,
      revenueResult,
      duesResult,
      paymentSummaryResult,
      leadsResult,
      membersResult,
    ] = await Promise.allSettled([
      apiFetch<DashboardSummary>(apiBaseUrl, '/api/v1/dashboard/summary', {
        token: accessToken,
        query,
      }),
      apiFetch<LeadFunnel>(apiBaseUrl, '/api/v1/dashboard/lead-funnel', {
        token: accessToken,
        query,
      }),
      apiFetch<RevenueBreakdown[]>(apiBaseUrl, '/api/v1/dashboard/revenue', {
        token: accessToken,
        query,
      }),
      apiFetch<DuesReport[]>(apiBaseUrl, '/api/v1/dashboard/dues', {
        token: accessToken,
        query,
      }),
      apiFetch<PaymentSummary>(apiBaseUrl, '/api/v1/payments/summary', {
        token: accessToken,
        query,
      }),
      apiFetch<Lead[]>(apiBaseUrl, '/api/v1/leads', {
        token: accessToken,
        query,
      }),
      apiFetch<Member[]>(apiBaseUrl, '/api/v1/members', {
        token: accessToken,
        query,
      }),
    ])

    if (summaryResult.status === 'fulfilled') {
      setSummary(summaryResult.value)
    }
    if (funnelResult.status === 'fulfilled') {
      setFunnel(funnelResult.value)
    }
    if (revenueResult.status === 'fulfilled') {
      setRevenue(revenueResult.value)
    }
    if (duesResult.status === 'fulfilled') {
      setDues(duesResult.value)
    }
    if (paymentSummaryResult.status === 'fulfilled') {
      setPaymentSummary(paymentSummaryResult.value)
    }
    if (leadsResult.status === 'fulfilled') {
      setLeads(leadsResult.value)
    }
    if (membersResult.status === 'fulfilled') {
      setMembers(membersResult.value)
    }

    const rejected = [
      summaryResult,
      funnelResult,
      revenueResult,
      duesResult,
      paymentSummaryResult,
      leadsResult,
      membersResult,
    ].filter((result) => result.status === 'rejected')

    if (rejected.length > 0) {
      const firstFailure = rejected[0]
      if (firstFailure.status === 'rejected') {
        pushNotice(
          'info',
          'Partial live data',
          errorMessage(firstFailure.reason),
        )
      }
    }

    setDataBusy(false)
  })

  useEffect(() => {
    void refreshHealth()
  }, [apiBaseUrl, refreshHealth])

  useEffect(() => {
    if (!accessToken) {
      setProfile(null)
      return
    }

    void refreshProfile(accessToken)
  }, [accessToken, apiBaseUrl, refreshProfile])

  useEffect(() => {
    void refreshLiveData()
  }, [accessToken, activeBranchId, apiBaseUrl, refreshLiveData])

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setAuthBusy(true)

    try {
      const tokens = await apiFetch<TokenResponse>(apiBaseUrl, '/api/v1/auth/login', {
        method: 'POST',
        body: { email, password },
      })

      const nextProfile = await apiFetch<UserProfile>(apiBaseUrl, '/api/v1/auth/me', {
        token: tokens.access_token,
      })

      startTransition(() => {
        setAccessToken(tokens.access_token)
        setRefreshToken(tokens.refresh_token)
        setTokenInput(tokens.access_token)
        setProfile(nextProfile)
      })

      pushNotice(
        'success',
        'Live session connected',
        `${nextProfile.full_name} is ready on branch ${nextProfile.branch_id.slice(0, 8)}.`,
      )
    } catch (error) {
      pushNotice('error', 'Login failed', errorMessage(error))
    } finally {
      setAuthBusy(false)
    }
  }

  async function handleManualTokenConnect() {
    if (!tokenInput.trim()) {
      pushNotice('error', 'Missing token', 'Paste a bearer token first.')
      return
    }

    setAccessToken(tokenInput.trim())
    await refreshProfile(tokenInput.trim())
    pushNotice('info', 'Token attached', 'Manual token saved for live requests.')
  }

  function handleLogout() {
    startTransition(() => {
      setAccessToken('')
      setRefreshToken('')
      setTokenInput('')
      setProfile(null)
      setBranchOverride('')
    })
    pushNotice('info', 'Session cleared', 'Local frontend state has been reset.')
  }

  async function handleOrganizationCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    try {
      const organization = await apiFetch<Organization>(
        apiBaseUrl,
        '/api/v1/organizations',
        {
          method: 'POST',
          body: organizationForm,
        },
      )
      setCreatedOrganization(organization)
      setBranchForm((current) => ({ ...current, org_id: organization.id }))
      setOrganizationForm(defaultOrganizationForm)
      pushNotice(
        'success',
        'Organization created',
        `${organization.name} is ready for branch setup.`,
      )
    } catch (error) {
      pushNotice('error', 'Organization create failed', errorMessage(error))
    }
  }

  async function handleBranchCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    try {
      const branch = await apiFetch<Branch>(apiBaseUrl, '/api/v1/branches', {
        method: 'POST',
        token: accessToken,
        query: { org_id: branchForm.org_id },
        body: {
          name: branchForm.name,
          address: branchForm.address,
          city: branchForm.city,
          phone: branchForm.phone,
        },
      })
      setCreatedBranch(branch)
      setBranchOverride(branch.id)
      setBranchForm((current) => ({ ...defaultBranchForm, org_id: current.org_id }))
      pushNotice(
        'success',
        'Branch created',
        `${branch.name} is now the active scope for owner requests.`,
      )
      await refreshLiveData()
    } catch (error) {
      pushNotice('error', 'Branch create failed', errorMessage(error))
    }
  }

  async function handleLeadCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    try {
      await apiFetch<Lead>(apiBaseUrl, '/api/v1/leads', {
        method: 'POST',
        token: accessToken,
        query: activeBranchId ? { branch_id: activeBranchId } : undefined,
        body: leadForm,
      })
      setLeadForm(defaultLeadForm)
      pushNotice(
        'success',
        'Lead dropped into the funnel',
        'The acquisition board was refreshed from the backend.',
      )
      await refreshLiveData()
    } catch (error) {
      pushNotice('error', 'Lead create failed', errorMessage(error))
    }
  }

  async function handleMemberCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    try {
      await apiFetch<Member>(apiBaseUrl, '/api/v1/members', {
        method: 'POST',
        token: accessToken,
        query: activeBranchId ? { branch_id: activeBranchId } : undefined,
        body: memberForm,
      })
      setMemberForm(defaultMemberForm)
      pushNotice(
        'success',
        'Member profile created',
        'The roster was refreshed from the backend.',
      )
      await refreshLiveData()
    } catch (error) {
      pushNotice('error', 'Member create failed', errorMessage(error))
    }
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />
      <div className="ambient ambient-c" />

      <header className="hero-panel surface">
        <div className="hero-copy">
          <span className="eyebrow">FlowOS frontend drop</span>
          <h1>Pulse deck for gym operators who hate boring dashboards.</h1>
          <p className="hero-text">
            A sharp control room for this FastAPI backend: bootstrap the org,
            connect a staff session, and pull revenue, funnel, roster, and dues
            data into one cinematic screen.
          </p>
        </div>

        <div className="hero-strip">
          <div className={`signal signal-${health}`}>
            <span className="signal-dot" />
            <div>
              <strong>{health === 'online' ? 'API online' : health === 'offline' ? 'API offline' : 'Checking API'}</strong>
              <p>{healthDetail}</p>
            </div>
          </div>

          <div className="hero-chip-grid">
            <div className="hero-chip">
              <span>Backend</span>
              <strong>FastAPI + SQLModel</strong>
            </div>
            <div className="hero-chip">
              <span>Frontend</span>
              <strong>React 19 + Vite</strong>
            </div>
            <div className="hero-chip">
              <span>Scope</span>
              <strong>{activeBranchId ? activeBranchId.slice(0, 8) : 'Awaiting branch'}</strong>
            </div>
          </div>
        </div>
      </header>

      {notices.length > 0 ? (
        <section className="notice-stack">
          {notices.map((notice) => (
            <article key={notice.id} className={`notice notice-${notice.tone}`}>
              <strong>{notice.title}</strong>
              <p>{notice.detail}</p>
            </article>
          ))}
        </section>
      ) : null}

      <main className="layout">
        <section className="surface control-grid">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Connect</span>
              <h2>Backend session control</h2>
            </div>
            <button
              className="ghost-button"
              type="button"
              onClick={() => {
                void refreshHealth()
                void refreshLiveData()
              }}
            >
              {dataBusy ? 'Refreshing…' : 'Refresh live data'}
            </button>
          </div>

          <div className="connection-layout">
            <div className="connection-card">
              <label className="field">
                <span>API base URL</span>
                <input
                  value={apiBaseUrl}
                  onChange={(event) => setApiBaseUrl(event.target.value)}
                  placeholder="http://localhost:8000"
                />
              </label>

              <form className="stack-form" onSubmit={handleLogin}>
                <label className="field">
                  <span>Staff email</span>
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="frontdesk@gym.com"
                  />
                </label>
                <label className="field">
                  <span>Password</span>
                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Enter password"
                  />
                </label>
                <div className="button-row">
                  <button className="primary-button" type="submit" disabled={authBusy}>
                    {authBusy ? 'Connecting…' : 'Login'}
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void refreshHealth()}
                  >
                    Ping API
                  </button>
                </div>
              </form>
            </div>

            <div className="connection-card">
              <label className="field">
                <span>Access token</span>
                <textarea
                  rows={5}
                  value={tokenInput}
                  onChange={(event) => setTokenInput(event.target.value)}
                  placeholder="Paste an existing bearer token if you do not want to login from the UI."
                />
              </label>

              <label className="field">
                <span>Owner branch override</span>
                <input
                  value={branchOverride}
                  onChange={(event) => setBranchOverride(event.target.value)}
                  placeholder="Optional branch_id for owner-scoped requests"
                />
              </label>

              <div className="button-row">
                <button
                  className="primary-button"
                  type="button"
                  onClick={() => void handleManualTokenConnect()}
                >
                  Use token
                </button>
                <button className="ghost-button" type="button" onClick={handleLogout}>
                  Clear session
                </button>
              </div>
            </div>
          </div>

          <div className="identity-bar">
            <div className="identity-pill">
              <span>Session</span>
              <strong>{liveDataReady ? 'Attached' : 'Guest mode'}</strong>
            </div>
            <div className="identity-pill">
              <span>Role</span>
              <strong>{profile ? formatRole(profile.role) : 'None'}</strong>
            </div>
            <div className="identity-pill">
              <span>Org</span>
              <strong>{profile?.org_id.slice(0, 8) ?? 'Bootstrap first'}</strong>
            </div>
            <div className="identity-pill">
              <span>Branch</span>
              <strong>{activeBranchId ? activeBranchId.slice(0, 8) : 'Set in token or override'}</strong>
            </div>
          </div>
        </section>

        <section className="surface analytics-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Live analytics</span>
              <h2>Operator snapshot</h2>
            </div>
            <p className="section-note">
              Manager and owner roles unlock the full dashboard suite. Front desk
              tokens still populate roster and dues-oriented views.
            </p>
          </div>

          <div className="metric-grid">
            {dashboardStatConfig.map((stat) => {
              const rawValue = Number(summary[stat.key] ?? 0)
              const display = stat.formatter ? stat.formatter(rawValue) : rawValue.toString()
              return (
                <article key={stat.key} className={`metric-card accent-${stat.accent}`}>
                  <span>{stat.label}</span>
                  <strong>{display}</strong>
                </article>
              )
            })}
          </div>

          <div className="analytics-layout">
            <article className="chart-card">
              <div className="mini-heading">
                <span>Revenue rhythm</span>
                <strong>Last {revenue.length || 30} days</strong>
              </div>
              <div className="bar-strip">
                {(revenue.length ? revenue : [{ date: 'No data', amount: 0, count: 0 }]).map(
                  (point) => {
                    const amount = Number(point.amount)
                    const maxAmount = Math.max(...revenue.map((item) => Number(item.amount)), 1)
                    const height = `${Math.max((amount / maxAmount) * 100, revenue.length ? 16 : 6)}%`

                    return (
                      <div key={`${point.date}-${point.count}`} className="bar-slot">
                        <div className="bar" style={{ height }} />
                        <span>{revenue.length ? formatDate(point.date) : 'Live data locked'}</span>
                      </div>
                    )
                  },
                )}
              </div>
            </article>

            <article className="funnel-card">
              <div className="mini-heading">
                <span>Lead funnel</span>
                <strong>{funnel.converted} converted</strong>
              </div>
              <div className="funnel-list">
                {Object.entries(funnel).map(([stage, count]) => (
                  <div key={stage} className="funnel-row">
                    <span>{formatRole(stage)}</span>
                    <strong>{count}</strong>
                  </div>
                ))}
              </div>
            </article>

            <article className="dues-card">
              <div className="mini-heading">
                <span>Collections pulse</span>
                <strong>
                  {paymentSummary
                    ? formatCurrency(paymentSummary.today_collection)
                    : 'Awaiting payment data'}
                </strong>
              </div>
              <div className="dues-summary">
                <p>
                  Outstanding dues:{' '}
                  <strong>
                    {paymentSummary
                      ? formatCurrency(paymentSummary.outstanding_dues)
                      : 'N/A'}
                  </strong>
                </p>
              </div>
              <ul className="dues-list">
                {dues.length > 0 ? (
                  dues.slice(0, 4).map((item) => (
                    <li key={item.member_id}>
                      <div>
                        <strong>{item.full_name}</strong>
                        <span>{item.days_overdue} days overdue</span>
                      </div>
                      <strong>{formatCurrency(item.amount_due)}</strong>
                    </li>
                  ))
                ) : (
                  <li className="empty-state">
                    <strong>No dues in view</strong>
                    <span>Connect a role with access or seed branch subscriptions.</span>
                  </li>
                )}
              </ul>
            </article>
          </div>
        </section>

        <section className="surface forms-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Bootstrap + intake</span>
              <h2>Real backend mutations</h2>
            </div>
            <p className="section-note">
              These forms hit the FastAPI routes directly. Organization creation
              is public; branch, lead, and member flows use the attached token.
            </p>
          </div>

          <div className="form-grid">
            <form className="action-card" onSubmit={handleOrganizationCreate}>
              <div className="mini-heading">
                <span>Step 01</span>
                <strong>Create organization</strong>
              </div>
              <label className="field">
                <span>Name</span>
                <input
                  value={organizationForm.name}
                  onChange={(event) =>
                    setOrganizationForm((current) => ({
                      ...current,
                      name: event.target.value,
                    }))
                  }
                  placeholder="Northline Gym"
                />
              </label>
              <label className="field">
                <span>Slug</span>
                <input
                  value={organizationForm.slug}
                  onChange={(event) =>
                    setOrganizationForm((current) => ({
                      ...current,
                      slug: event.target.value,
                    }))
                  }
                  placeholder="northline-gym"
                />
              </label>
              <label className="field">
                <span>Owner email</span>
                <input
                  type="email"
                  value={organizationForm.owner_email}
                  onChange={(event) =>
                    setOrganizationForm((current) => ({
                      ...current,
                      owner_email: event.target.value,
                    }))
                  }
                  placeholder="owner@gym.com"
                />
              </label>
              <label className="field">
                <span>Phone</span>
                <input
                  value={organizationForm.phone ?? ''}
                  onChange={(event) =>
                    setOrganizationForm((current) => ({
                      ...current,
                      phone: event.target.value,
                    }))
                  }
                  placeholder="+91 98xxxxxx"
                />
              </label>
              <button className="primary-button" type="submit">
                Launch organization
              </button>
            </form>

            <form className="action-card" onSubmit={handleBranchCreate}>
              <div className="mini-heading">
                <span>Step 02</span>
                <strong>Create branch</strong>
              </div>
              <label className="field">
                <span>Organization ID</span>
                <input
                  value={branchForm.org_id}
                  onChange={(event) =>
                    setBranchForm((current) => ({
                      ...current,
                      org_id: event.target.value,
                    }))
                  }
                  placeholder="Paste org_id or create one above"
                />
              </label>
              <label className="field">
                <span>Branch name</span>
                <input
                  value={branchForm.name}
                  onChange={(event) =>
                    setBranchForm((current) => ({
                      ...current,
                      name: event.target.value,
                    }))
                  }
                  placeholder="Downtown Performance Lab"
                />
              </label>
              <label className="field">
                <span>City</span>
                <input
                  value={branchForm.city ?? ''}
                  onChange={(event) =>
                    setBranchForm((current) => ({
                      ...current,
                      city: event.target.value,
                    }))
                  }
                  placeholder="Kathmandu"
                />
              </label>
              <label className="field">
                <span>Address</span>
                <input
                  value={branchForm.address ?? ''}
                  onChange={(event) =>
                    setBranchForm((current) => ({
                      ...current,
                      address: event.target.value,
                    }))
                  }
                  placeholder="3rd floor, main road"
                />
              </label>
              <button className="primary-button" type="submit">
                Open branch
              </button>
            </form>

            <form className="action-card" onSubmit={handleLeadCreate}>
              <div className="mini-heading">
                <span>Step 03</span>
                <strong>Capture lead</strong>
              </div>
              <label className="field">
                <span>Full name</span>
                <input
                  value={leadForm.full_name}
                  onChange={(event) =>
                    setLeadForm((current) => ({
                      ...current,
                      full_name: event.target.value,
                    }))
                  }
                  placeholder="Aarya Shrestha"
                />
              </label>
              <label className="field">
                <span>Phone</span>
                <input
                  value={leadForm.phone}
                  onChange={(event) =>
                    setLeadForm((current) => ({
                      ...current,
                      phone: event.target.value,
                    }))
                  }
                  placeholder="98xxxxxx"
                />
              </label>
              <label className="field">
                <span>Email</span>
                <input
                  type="email"
                  value={leadForm.email ?? ''}
                  onChange={(event) =>
                    setLeadForm((current) => ({
                      ...current,
                      email: event.target.value,
                    }))
                  }
                  placeholder="lead@example.com"
                />
              </label>
              <label className="field">
                <span>Source</span>
                <input
                  value={leadForm.source ?? ''}
                  onChange={(event) =>
                    setLeadForm((current) => ({
                      ...current,
                      source: event.target.value,
                    }))
                  }
                  placeholder="Instagram reel"
                />
              </label>
              <button className="primary-button" type="submit">
                Add to funnel
              </button>
            </form>

            <form className="action-card" onSubmit={handleMemberCreate}>
              <div className="mini-heading">
                <span>Step 04</span>
                <strong>Create member</strong>
              </div>
              <label className="field">
                <span>Full name</span>
                <input
                  value={memberForm.full_name}
                  onChange={(event) =>
                    setMemberForm((current) => ({
                      ...current,
                      full_name: event.target.value,
                    }))
                  }
                  placeholder="Riya Basnet"
                />
              </label>
              <label className="field">
                <span>Phone</span>
                <input
                  value={memberForm.phone}
                  onChange={(event) =>
                    setMemberForm((current) => ({
                      ...current,
                      phone: event.target.value,
                    }))
                  }
                  placeholder="98xxxxxx"
                />
              </label>
              <label className="field">
                <span>Email</span>
                <input
                  type="email"
                  value={memberForm.email ?? ''}
                  onChange={(event) =>
                    setMemberForm((current) => ({
                      ...current,
                      email: event.target.value,
                    }))
                  }
                  placeholder="member@example.com"
                />
              </label>
              <label className="field">
                <span>Gender</span>
                <input
                  value={memberForm.gender ?? ''}
                  onChange={(event) =>
                    setMemberForm((current) => ({
                      ...current,
                      gender: event.target.value,
                    }))
                  }
                  placeholder="Optional"
                />
              </label>
              <button className="primary-button" type="submit">
                Add to roster
              </button>
            </form>
          </div>
        </section>

        <section className="surface roster-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Rosters</span>
              <h2>Leads and members in motion</h2>
            </div>
            <p className="section-note">
              Search is client-side for fast scanning, while the lists themselves
              are pulled from the backend.
            </p>
          </div>

          <div className="roster-layout">
            <article className="table-card">
              <div className="mini-heading">
                <span>Lead pipeline</span>
                <strong>{filteredLeads.length} visible</strong>
              </div>
              <label className="field inline-field">
                <span>Search leads</span>
                <input
                  value={leadSearch}
                  onChange={(event) => setLeadSearch(event.target.value)}
                  placeholder="Name, phone, or status"
                />
              </label>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Status</th>
                      <th>Phone</th>
                      <th>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredLeads.length > 0 ? (
                      filteredLeads.slice(0, 8).map((lead) => (
                        <tr key={lead.id}>
                          <td>{lead.full_name}</td>
                          <td>
                            <span className="tag">{formatRole(lead.status)}</span>
                          </td>
                          <td>{lead.phone}</td>
                          <td>{formatDate(lead.created_at)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="empty-row">
                          No lead records yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </article>

            <article className="table-card">
              <div className="mini-heading">
                <span>Member roster</span>
                <strong>{filteredMembers.length} visible</strong>
              </div>
              <label className="field inline-field">
                <span>Search members</span>
                <input
                  value={memberSearch}
                  onChange={(event) => setMemberSearch(event.target.value)}
                  placeholder="Name, member code, status"
                />
              </label>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Status</th>
                      <th>Member code</th>
                      <th>Joined</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredMembers.length > 0 ? (
                      filteredMembers.slice(0, 8).map((member) => (
                        <tr key={member.id}>
                          <td>{member.full_name}</td>
                          <td>
                            <span className="tag">{formatRole(member.status)}</span>
                          </td>
                          <td>{member.member_code}</td>
                          <td>{formatDate(member.created_at)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="empty-row">
                          No member records yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </article>
          </div>
        </section>

        <section className="surface atlas-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Backend atlas</span>
              <h2>Module map for the rest of the buildout</h2>
            </div>
            <div className="atlas-meta">
              <div>
                <span>Created org</span>
                <strong>{createdOrganization?.name ?? 'None yet'}</strong>
              </div>
              <div>
                <span>Created branch</span>
                <strong>{createdBranch?.name ?? 'None yet'}</strong>
              </div>
            </div>
          </div>

          <div className="atlas-grid">
            {moduleAtlas.map((module) => (
              <article key={module.label} className="atlas-card">
                <span className="atlas-label">{module.label}</span>
                <p>{module.caption}</p>
                <ul>
                  {module.endpoints.map((endpoint) => (
                    <li key={endpoint}>{endpoint}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
