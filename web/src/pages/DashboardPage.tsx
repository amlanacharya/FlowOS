import { useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { DashboardSummary, DuesReport, LeadFunnel, RevenueBreakdown } from '../types'
import { formatCurrency, formatDate, formatRole, errorMessage } from '../utils'
import { SkeletonKpiGrid } from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

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
    ]).then(([summaryResult, funnelResult, revenueResult, duesResult]) => {
      if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value)
      if (funnelResult.status === 'fulfilled') setFunnel(funnelResult.value)
      if (revenueResult.status === 'fulfilled') setRevenue(revenueResult.value)
      if (duesResult.status === 'fulfilled') setDues(duesResult.value)

      const firstFailure = [summaryResult, funnelResult, revenueResult, duesResult].find((result) => result.status === 'rejected')
      if (firstFailure?.status === 'rejected') {
        pushNotice('info', 'Partial data loaded', errorMessage(firstFailure.reason))
      }

      setLoading(false)
    })
  }, [accessToken, apiBaseUrl, branchId, pushNotice])

  const summaryCards = [
    {
      label: 'Active roster',
      value: summary.active_members.toString(),
      note: `${summary.inactive_members} inactive members still need follow-up.`,
    },
    {
      label: 'Revenue month to date',
      value: formatCurrency(summary.total_revenue_mtd),
      note: `${formatCurrency(summary.collections_today)} collected today.`,
    },
    {
      label: 'Outstanding dues',
      value: formatCurrency(summary.outstanding_dues),
      note: `${summary.renewals_due_7_days} renewals are due in the next 7 days.`,
    },
  ]

  const maxRevenue = Math.max(...revenue.map((point) => Number(point.amount)), 1)
  const funnelEntries = Object.entries(funnel) as [string, number][]
  const maxFunnel = Math.max(...funnelEntries.map(([, count]) => count), 1)
  const todayLabel = new Intl.DateTimeFormat('en-IN', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  }).format(new Date())

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Operations overview</div>
          <div className="page-title">Dashboard</div>
          <div className="page-sub">
            Track memberships, trials, dues, and collections for {todayLabel}.
          </div>
        </div>

        <div className="page-actions">
          <span className="badge badge-active">{branchId ? 'Branch scoped' : 'All branches'}</span>
          <span className="badge badge-new">{summary.classes_today} classes today</span>
        </div>
      </div>

      <div className="page-body">
        {summary.renewals_due_7_days > 0 && (
          <div className="alert-strip animate-in">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <span>
              <strong>{summary.renewals_due_7_days}</strong> memberships expire within 7 days. Queue those calls before close.
            </span>
          </div>
        )}

        {loading ? (
          <SkeletonKpiGrid />
        ) : (
          <div className="summary-row">
            {summaryCards.map((card, index) => (
              <div key={card.label} className={`summary-card animate-in delay-${index + 1}`}>
                <div className="summary-label">{card.label}</div>
                <div className="summary-amount">{card.value}</div>
                <div className="summary-note">{card.note}</div>
              </div>
            ))}
          </div>
        )}

        <div className="hero-grid">
          <div className="card animate-in delay-2">
            <div className="card-header">
              <span className="card-title">Revenue run-rate</span>
              <span className="card-meta">Last {revenue.length || 30} days</span>
            </div>
            <div className="card-body">
              {loading ? (
                <div className="skeleton skeleton-chart" />
              ) : revenue.length > 0 ? (
                <div className="bar-chart">
                  {revenue.map((point) => {
                    const height = Math.max((Number(point.amount) / maxRevenue) * 100, 6)
                    return (
                      <div key={point.date} className="bar-slot">
                        <div
                          className="bar-fill"
                          style={{ height: `${height}%` }}
                          data-tip={formatCurrency(Number(point.amount))}
                        />
                        <span className="bar-label">{formatDate(point.date).split(' ')[0]}</span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="empty-row">Revenue history will appear here as collections come in.</div>
              )}
            </div>
          </div>

          <div className="card animate-in delay-3">
            <div className="card-header">
              <span className="card-title">Lead pipeline</span>
              <span className="card-meta">{summary.trials_converted} conversions this week</span>
            </div>
            <div className="card-body">
              {loading ? (
                <div className="skeleton skeleton-chart" />
              ) : funnelEntries.some(([, count]) => count > 0) ? (
                <div className="funnel-list">
                  {funnelEntries.map(([stage, count]) => (
                    <div key={stage} className="funnel-row">
                      <span className="funnel-label">{formatRole(stage)}</span>
                      <div className="funnel-bar-track">
                        <div
                          className="funnel-bar-fill"
                          style={{ width: `${Math.max((count / maxFunnel) * 100, count > 0 ? 8 : 0)}%` }}
                        />
                      </div>
                      <span className="funnel-count">{count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-row">Lead movement will show once the funnel starts filling.</div>
              )}
            </div>
          </div>
        </div>

        <div className="split-grid">
          <div className="card animate-in delay-4">
            <div className="card-header">
              <span className="card-title">Collections watchlist</span>
              <span className="card-meta">{dues.length} members flagged</span>
            </div>
            <div className="card-body">
              {loading ? (
                <div className="skeleton skeleton-chart" />
              ) : dues.length > 0 ? (
                <div className="dues-list">
                  {dues.slice(0, 6).map((item) => (
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
                <div className="empty-row">No dues are pending. Collections are current.</div>
              )}
            </div>
          </div>

          <div className="card animate-in delay-5">
            <div className="card-header">
              <span className="card-title">Today&apos;s rhythm</span>
              <span className="card-meta">Live operating signals</span>
            </div>
            <div className="card-body">
              <div className="info-row">
                <div>
                  <div className="table-name">Class fill rate</div>
                  <div className="info-key">How close the schedule is to capacity</div>
                </div>
                <div className="info-val">{Math.round(summary.class_fill_rate)}%</div>
              </div>
              <div className="info-row">
                <div>
                  <div className="table-name">Leads this week</div>
                  <div className="info-key">New demand entering the funnel</div>
                </div>
                <div className="info-val">{summary.leads_this_week}</div>
              </div>
              <div className="info-row">
                <div>
                  <div className="table-name">Trials scheduled</div>
                  <div className="info-key">Booked sessions that need confirmation</div>
                </div>
                <div className="info-val">{summary.trials_scheduled}</div>
              </div>
              <div className="info-row">
                <div>
                  <div className="table-name">Collections today</div>
                  <div className="info-key">Cash already landed before close</div>
                </div>
                <div className="info-val">{formatCurrency(summary.collections_today)}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
