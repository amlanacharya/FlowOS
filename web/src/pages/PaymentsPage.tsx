import { type FormEvent, useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../api'
import type { DuesReport, PaymentSummary, RevenueBreakdown } from '../types'
import { errorMessage, formatCurrency, formatDate } from '../utils'
import Skeleton from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

type Payment = {
  id: string
  member_id: string
  amount: number
  mode: string
  payment_date: string
  created_at: string
  notes?: string
}

type MemberOption = {
  id: string
  full_name: string
}

export default function PaymentsPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState<PaymentSummary | null>(null)
  const [dues, setDues] = useState<DuesReport[]>([])
  const [revenue, setRevenue] = useState<RevenueBreakdown[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [members, setMembers] = useState<MemberOption[]>([])
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [form, setForm] = useState({
    member_id: '',
    amount: '',
    mode: 'cash',
    notes: '',
  })

  const query = useMemo(() => (branchId ? { branch_id: branchId } : undefined), [branchId])

  useEffect(() => {
    void Promise.allSettled([
      apiFetch<PaymentSummary>(apiBaseUrl, '/api/v1/payments/summary', { token: accessToken, query }),
      apiFetch<DuesReport[]>(apiBaseUrl, '/api/v1/dashboard/dues', { token: accessToken, query }),
      apiFetch<RevenueBreakdown[]>(apiBaseUrl, '/api/v1/dashboard/revenue', { token: accessToken, query }),
      apiFetch<Payment[]>(apiBaseUrl, '/api/v1/payments', { token: accessToken, query }),
      apiFetch<MemberOption[]>(apiBaseUrl, '/api/v1/members', { token: accessToken, query }),
    ]).then(([summaryResult, duesResult, revenueResult, paymentResult, memberResult]) => {
      if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value)
      if (duesResult.status === 'fulfilled') setDues(duesResult.value)
      if (revenueResult.status === 'fulfilled') setRevenue(revenueResult.value)
      if (paymentResult.status === 'fulfilled') setPayments(paymentResult.value)
      if (memberResult.status === 'fulfilled') setMembers(memberResult.value)

      const firstFailure = [summaryResult, duesResult, revenueResult, paymentResult, memberResult].find((result) => result.status === 'rejected')
      if (firstFailure?.status === 'rejected') {
        pushNotice('info', 'Partial data loaded', errorMessage(firstFailure.reason))
      }

      setLoading(false)
    })
  }, [accessToken, apiBaseUrl, query, pushNotice])

  const mtdRevenue = revenue.reduce((sum, point) => sum + Number(point.amount), 0)
  const membersById = new Map(members.map((member) => [member.id, member.full_name]))

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)

    try {
      await apiFetch(apiBaseUrl, '/api/v1/payments', {
        method: 'POST',
        token: accessToken,
        query,
        body: {
          member_id: form.member_id,
          amount: Number(form.amount),
          mode: form.mode,
          notes: form.notes || undefined,
        },
      })

      setForm({ member_id: '', amount: '', mode: 'cash', notes: '' })
      setDrawerOpen(false)
      pushNotice('success', 'Payment recorded', `${formatCurrency(Number(form.amount))} captured via ${form.mode}.`)

      const [summaryResult, duesResult, revenueResult, paymentResult] = await Promise.allSettled([
        apiFetch<PaymentSummary>(apiBaseUrl, '/api/v1/payments/summary', { token: accessToken, query }),
        apiFetch<DuesReport[]>(apiBaseUrl, '/api/v1/dashboard/dues', { token: accessToken, query }),
        apiFetch<RevenueBreakdown[]>(apiBaseUrl, '/api/v1/dashboard/revenue', { token: accessToken, query }),
        apiFetch<Payment[]>(apiBaseUrl, '/api/v1/payments', { token: accessToken, query }),
      ])

      if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value)
      if (duesResult.status === 'fulfilled') setDues(duesResult.value)
      if (revenueResult.status === 'fulfilled') setRevenue(revenueResult.value)
      if (paymentResult.status === 'fulfilled') setPayments(paymentResult.value)
    } catch (error) {
      pushNotice('error', 'Payment failed', errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Collections desk</div>
          <div className="page-title">Payments</div>
          <div className="page-sub">
            Watch daily cash movement, record collections fast, and keep overdue accounts visible before they drift.
          </div>
        </div>

        <div className="page-actions">
          <span className="badge badge-active">{payments.length} receipts</span>
          <button className="btn btn-primary" type="button" onClick={() => setDrawerOpen(true)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Record payment
          </button>
        </div>
      </div>

      <div className="page-body">
        <div className="summary-row">
          {loading ? (
            <>
              <Skeleton variant="kpi" />
              <Skeleton variant="kpi" />
              <Skeleton variant="kpi" />
            </>
          ) : (
            <>
              <div className="summary-card animate-in delay-1">
                <div className="summary-label">Today&apos;s collections</div>
                <div className="summary-amount text-success">
                  {summary ? formatCurrency(summary.today_collection) : formatCurrency(0)}
                </div>
                <div className="summary-note">Fresh cash already closed out during this shift.</div>
              </div>

              <div className="summary-card animate-in delay-2">
                <div className="summary-label">Revenue month to date</div>
                <div className="summary-amount">{formatCurrency(mtdRevenue)}</div>
                <div className="summary-note">Net collected over the current dashboard revenue window.</div>
              </div>

              <div className="summary-card animate-in delay-3">
                <div className="summary-label">Outstanding dues</div>
                <div className="summary-amount text-error">
                  {summary ? formatCurrency(summary.outstanding_dues) : formatCurrency(0)}
                </div>
                <div className="summary-note">Accounts still waiting on recovery action from staff.</div>
              </div>
            </>
          )}
        </div>

        <div className="split-grid">
          <div className="card animate-in delay-2">
            <div className="card-header">
              <span className="card-title">Recent payments</span>
              <span className="card-meta">Latest 10 receipts</span>
            </div>

            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Member</th>
                    <th>Amount</th>
                    <th>Mode</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    Array.from({ length: 5 }).map((_, index) => (
                      <tr key={index}>
                        <td colSpan={4} style={{ padding: '12px 14px' }}>
                          <Skeleton variant="text" />
                        </td>
                      </tr>
                    ))
                  ) : payments.length > 0 ? (
                    payments.slice(0, 10).map((payment) => (
                      <tr key={payment.id}>
                        <td>
                          <div className="table-name">{membersById.get(payment.member_id) || 'Member record'}</div>
                          <div className="table-sub mono">{payment.member_id.slice(0, 8)}</div>
                        </td>
                        <td className="table-name text-success">{formatCurrency(Number(payment.amount))}</td>
                        <td>
                          <span className="badge badge-active">{payment.mode.replaceAll('_', ' ')}</span>
                        </td>
                        <td>{formatDate(payment.payment_date)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="empty-row">
                        No payments recorded yet. Use the drawer to capture the first receipt.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card animate-in delay-3">
            <div className="card-header">
              <span className="card-title">Recovery watchlist</span>
              <span className="card-meta">{dues.length} members pending</span>
            </div>
            <div className="card-body">
              {loading ? (
                <div className="skeleton skeleton-chart" />
              ) : dues.length > 0 ? (
                <div className="dues-list">
                  {dues.slice(0, 8).map((item) => (
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
                <div className="empty-row">No overdue balances. Collections are caught up.</div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className={`drawer-overlay ${drawerOpen ? 'open' : ''}`} onClick={() => setDrawerOpen(false)} />
      <div className={`drawer ${drawerOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <span className="drawer-title">Record payment</span>
          <button className="btn-icon" type="button" onClick={() => setDrawerOpen(false)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'contents' }}>
          <div className="drawer-body">
            <div className="field">
              <label className="field-label" htmlFor="payment-member">Member</label>
              <select
                id="payment-member"
                value={form.member_id}
                onChange={(event) => setForm((current) => ({ ...current, member_id: event.target.value }))}
                required
              >
                <option value="">Select a member</option>
                {members.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.full_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label className="field-label" htmlFor="payment-amount">Amount</label>
              <input
                id="payment-amount"
                type="number"
                min="1"
                value={form.amount}
                onChange={(event) => setForm((current) => ({ ...current, amount: event.target.value }))}
                placeholder="1500"
                required
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="payment-mode">Payment mode</label>
              <select
                id="payment-mode"
                value={form.mode}
                onChange={(event) => setForm((current) => ({ ...current, mode: event.target.value }))}
              >
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="upi">UPI</option>
                <option value="bank_transfer">Bank transfer</option>
              </select>
            </div>

            <div className="field">
              <label className="field-label" htmlFor="payment-notes">Notes</label>
              <input
                id="payment-notes"
                value={form.notes}
                onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
                placeholder="Receipt number, partial payment note, collector name"
              />
              <div className="field-hint">
                Capture any details staff will need when reconciling later in the day.
              </div>
            </div>
          </div>

          <div className="drawer-footer">
            <button className="btn btn-primary" type="submit" disabled={submitting} style={{ flex: 1 }}>
              {submitting ? 'Recording...' : 'Record payment'}
            </button>
            <button className="btn btn-ghost" type="button" onClick={() => setDrawerOpen(false)}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </>
  )
}
