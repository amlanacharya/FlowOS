import { useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { DashboardSummary, DuesReport, LeadFunnel, RevenueBreakdown } from '../types'
import { formatCurrency, formatDate, formatRole } from '../utils'
import { SkeletonKpiGrid } from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'
import { errorMessage } from '../utils'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const defaultSummary: DashboardSummary = {
  active_members: 0, total_revenue_mtd: 0, leads_this_week: 0,
  trials_scheduled: 0, trials_converted: 0, renewals_due_7_days: 0,
  collections_today: 0, outstanding_dues: 0, classes_today: 0,
  class_fill_rate: 0, inactive_members: 0,
}

const defaultFunnel: LeadFunnel = {
  new: 0, contacted: 0, trial_scheduled: 0,
  trial_attended: 0, converted: 0, lost: 0,
}

const funnelColors = ['#3b82f6','#f97316','#a855f7','#14b8a6','#22c55e','#ef4444']

export default function DashboardPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState<DashboardSummary>(defaultSummary)
  const [funnel, setFunnel] = useState<LeadFunnel>(defaultFunnel)
  const [revenue, setRevenue] = useState<RevenueBreakdown[]>([])
  const [dues, setDues] = useState<DuesReport[]>([])

  useEffect(() => {
    const query = branchId ? { branch_id: branchId } : undefined

    void Promise.allSettled([
      apiFetch<DashboardSummary>(apiBaseUrl, '/api/v1/dashboard/summary', { token: accessToken, query }),
      apiFetch<LeadFunnel>(apiBaseUrl, '/api/v1/dashboard/lead-funnel', { token: accessToken, query }),
      apiFetch<RevenueBreakdown[]>(apiBaseUrl, '/api/v1/dashboard/revenue', { token: accessToken, query }),
      apiFetch<DuesReport[]>(apiBaseUrl, '/api/v1/dashboard/dues', { token: accessToken, query }),
    ]).then(([s, f, r, d]) => {
      if (s.status === 'fulfilled') setSummary(s.value)
      if (f.status === 'fulfilled') setFunnel(f.value)
      if (r.status === 'fulfilled') setRevenue(r.value)
      if (d.status === 'fulfilled') setDues(d.value)
      const firstFail = [s, f, r, d].find((x) => x.status === 'rejected')
      if (firstFail?.status === 'rejected') {
        pushNotice('info', 'Partial data', errorMessage(firstFail.reason))
      }
      setLoading(false)
    })
  }, [apiBaseUrl, accessToken, branchId])

  const kpiCards = [
    { label: 'Active Members',    value: summary.active_members,       accent: 'violet', sub: `${summary.inactive_members} inactive` },
    { label: 'Revenue MTD',       value: formatCurrency(summary.total_revenue_mtd), accent: 'cyan', sub: `${formatCurrency(summary.collections_today)} today` },
    { label: 'Leads This Week',   value: summary.leads_this_week,      accent: 'orange', sub: `${summary.trials_scheduled} trials scheduled` },
    { label: 'Classes Today',     value: summary.classes_today,        accent: 'purple', sub: `${Math.round(summary.class_fill_rate)}% fill rate` },
    { label: 'Renewals Due (7d)', value: summary.renewals_due_7_days,  accent: 'red',    sub: 'Action required' },
    { label: 'Outstanding Dues',  value: formatCurrency(summary.outstanding_dues), accent: 'green', sub: `${summary.trials_converted} converted leads` },
  ]

  const maxRevenue = Math.max(...revenue.map((r) => Number(r.amount)), 1)
  const funnelEntries = Object.entries(funnel) as [string, number][]
  const maxFunnel = Math.max(...funnelEntries.map(([, v]) => v), 1)

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">DASHBOARD</div>
          <div className="page-sub">Operations overview — {new Date().toLocaleDateString('en-IN', { weekday: 'long', month: 'long', day: 'numeric' })}</div>
        </div>
      </div>

      <div className="page-body">
        {summary.renewals_due_7_days > 0 && (
          <div className="alert-strip animate-in">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <span><strong>{summary.renewals_due_7_days}</strong> memberships expiring in the next 7 days — follow up now.</span>
          </div>
        )}

        {loading ? (
          <SkeletonKpiGrid />
        ) : (
          <div className="kpi-grid">
            {kpiCards.map((card, i) => (
              <div key={card.label} className={`kpi-card kpi-accent-${card.accent} animate-in delay-${i + 1}`}>
                <div className="kpi-label">{card.label}</div>
                <div className="kpi-value">{card.value}</div>
                <div className="kpi-sub">{card.sub}</div>
              </div>
            ))}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
          {/* Revenue chart */}
          <div className="card animate-in delay-3">
            <div className="card-header">
              <span className="card-title">Revenue — last {revenue.length || 30} days</span>
              <span style={{ fontSize: 11, color: 'var(--text-lo)' }}>Daily collections</span>
            </div>
            <div className="card-body">
              {loading ? (
                <div className="skeleton skeleton-chart" />
              ) : revenue.length > 0 ? (
                <div className="bar-chart">
                  {revenue.map((point) => {
                    const pct = Math.max((Number(point.amount) / maxRevenue) * 100, 2)
                    return (
                      <div key={point.date} className="bar-slot">
                        <div
                          className="bar-fill"
                          style={{ height: `${pct}%` }}
                          data-tip={formatCurrency(Number(point.amount))}
                        />
                        <span className="bar-label">{formatDate(point.date).split(' ')[0]}</span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div style={{ height: 120, display: 'grid', placeItems: 'center', color: 'var(--text-lo)', fontSize: 13 }}>
                  No revenue data yet
                </div>
              )}
            </div>
          </div>

          {/* Lead funnel */}
          <div className="card animate-in delay-4">
            <div className="card-header">
              <span className="card-title">Lead funnel</span>
              <span style={{ fontSize: 11, color: 'var(--text-lo)' }}>{funnel.converted} converted</span>
            </div>
            <div className="card-body">
              {loading ? (
                <div className="skeleton skeleton-chart" />
              ) : (
                <div className="funnel-list">
                  {funnelEntries.map(([stage, count], i) => (
                    <div key={stage} className="funnel-row">
                      <span className="funnel-label">{formatRole(stage)}</span>
                      <div className="funnel-bar-track">
                        <div
                          className="funnel-bar-fill"
                          style={{
                            width: `${(count / maxFunnel) * 100}%`,
                            background: funnelColors[i % funnelColors.length],
                          }}
                        />
                      </div>
                      <span className="funnel-count">{count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Dues */}
        <div className="card animate-in delay-5">
          <div className="card-header">
            <span className="card-title">Outstanding dues</span>
            <span style={{ fontSize: 11, color: 'var(--text-lo)' }}>{dues.length} members</span>
          </div>
          <div className="card-body">
            {loading ? (
              <div className="skeleton skeleton-chart" />
            ) : dues.length > 0 ? (
              <div className="dues-list">
                {dues.slice(0, 5).map((item) => (
                  <div key={item.member_id} className="dues-row">
                    <div>
                      <div className="dues-name">{item.full_name}</div>
                      <div className="dues-meta">{item.days_overdue} days overdue</div>
                    </div>
                    <div className="dues-amount">{formatCurrency(item.amount_due)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: 'var(--text-lo)', fontSize: 13, padding: '16px 0' }}>
                No outstanding dues — all members are current.
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
