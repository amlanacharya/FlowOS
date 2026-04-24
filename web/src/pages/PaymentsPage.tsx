import { useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { DuesReport, PaymentSummary, RevenueBreakdown } from '../types'
import { formatCurrency, formatDate, errorMessage } from '../utils'
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

  const query = branchId ? { branch_id: branchId } : undefined

  useEffect(() => {
    void Promise.allSettled([
      apiFetch<PaymentSummary>(apiBaseUrl, '/api/v1/payments/summary', { token: accessToken, query }),
      apiFetch<DuesReport[]>(apiBaseUrl, '/api/v1/dashboard/dues', { token: accessToken, query }),
      apiFetch<RevenueBreakdown[]>(apiBaseUrl, '/api/v1/dashboard/revenue', { token: accessToken, query }),
      apiFetch<Payment[]>(apiBaseUrl, '/api/v1/payments', { token: accessToken, query }),
      apiFetch<MemberOption[]>(apiBaseUrl, '/api/v1/members', { token: accessToken, query }),
    ]).then(([s, d, r, p, m]) => {
      if (s.status === 'fulfilled') setSummary(s.value)
      if (d.status === 'fulfilled') setDues(d.value)
      if (r.status === 'fulfilled') setRevenue(r.value)
      if (p.status === 'fulfilled') setPayments(p.value)
      if (m.status === 'fulfilled') setMembers(m.value)
      setLoading(false)
    })
  }, [apiBaseUrl, accessToken, branchId])

  const mtdRevenue = revenue.reduce((sum, r) => sum + Number(r.amount), 0)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
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
      pushNotice('success', 'Payment recorded', `₹${form.amount} via ${form.mode}.`)
      const [s, p] = await Promise.allSettled([
        apiFetch<PaymentSummary>(apiBaseUrl, '/api/v1/payments/summary', { token: accessToken, query }),
        apiFetch<Payment[]>(apiBaseUrl, '/api/v1/payments', { token: accessToken, query }),
      ])
      if (s.status === 'fulfilled') setSummary(s.value)
      if (p.status === 'fulfilled') setPayments(p.value)
    } catch (err) {
      pushNotice('error', 'Payment failed', errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">PAYMENTS</div>
          <div className="page-sub">Collections, dues, and revenue tracking</div>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" type="button" onClick={() => setDrawerOpen(true)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Record payment
          </button>
        </div>
      </div>

      <div className="page-body">
        {/* Summary cards */}
        <div className="summary-row animate-in">
          {loading ? (
            <>
              <Skeleton variant="kpi" /><Skeleton variant="kpi" /><Skeleton variant="kpi" />
            </>
          ) : (
            <>
              <div className="summary-card">
                <div className="summary-amount text-success">{summary ? formatCurrency(summary.today_collection) : '₹0'}</div>
                <div className="summary-label">Today's collections</div>
              </div>
              <div className="summary-card">
                <div className="summary-amount" style={{ color: 'var(--cyan)' }}>{formatCurrency(mtdRevenue)}</div>
                <div className="summary-label">Revenue MTD</div>
              </div>
              <div className="summary-card">
                <div className="summary-amount text-error">{summary ? formatCurrency(summary.outstanding_dues) : '₹0'}</div>
                <div className="summary-label">Outstanding dues</div>
              </div>
            </>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {/* Recent payments */}
          <div className="card animate-in delay-2">
            <div className="card-header">
              <span className="card-title">Recent payments</span>
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
                    Array.from({ length: 5 }).map((_, i) => (
                      <tr key={i}><td colSpan={4} style={{ padding: '8px 16px' }}><Skeleton variant="text" /></td></tr>
                    ))
                  ) : payments.length > 0 ? (
                    payments.slice(0, 10).map((p) => (
                      <tr key={p.id}>
                        <td style={{ color: 'var(--text-mid)', fontSize: 12, fontFamily: 'monospace' }}>{p.member_id.slice(0, 8)}</td>
                        <td><span style={{ fontFamily: 'var(--font-display)', fontSize: 16, color: 'var(--success)', letterSpacing: '0.5px' }}>{formatCurrency(Number(p.amount))}</span></td>
                        <td><span className="badge badge-active" style={{ textTransform: 'uppercase', letterSpacing: '0.5px' }}>{p.mode}</span></td>
                        <td style={{ color: 'var(--text-lo)' }}>{formatDate(p.created_at)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan={4} className="empty-row">No payments recorded yet.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Dues */}
          <div className="card animate-in delay-3">
            <div className="card-header">
              <span className="card-title">Outstanding dues</span>
              <span style={{ fontSize: 11, color: 'var(--text-lo)' }}>{dues.length} members</span>
            </div>
            <div className="card-body">
              {loading ? (
                <Skeleton variant="chart" />
              ) : dues.length > 0 ? (
                <div className="dues-list">
                  {dues.map((item) => (
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
                  No outstanding dues — all caught up.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Drawer */}
      <div className={`drawer-overlay ${drawerOpen ? 'open' : ''}`} onClick={() => setDrawerOpen(false)} />
      <div className={`drawer ${drawerOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <span className="drawer-title">RECORD PAYMENT</span>
          <button className="btn-icon" type="button" onClick={() => setDrawerOpen(false)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <form onSubmit={handleSubmit} style={{ display: 'contents' }}>
          <div className="drawer-body">
            <div className="field">
              <label className="field-label">Member *</label>
              <select value={form.member_id} onChange={(e) => setForm((f) => ({ ...f, member_id: e.target.value }))} required>
                <option value="">Select a member</option>
                {members.map((m) => (
                  <option key={m.id} value={m.id}>{m.full_name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field-label">Amount (₹) *</label>
              <input type="number" min="1" value={form.amount} onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))} placeholder="1500" required />
            </div>
            <div className="field">
              <label className="field-label">Payment mode</label>
              <select value={form.mode} onChange={(e) => setForm((f) => ({ ...f, mode: e.target.value }))}>
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="upi">UPI</option>
                <option value="bank_transfer">Bank transfer</option>
              </select>
            </div>
            <div className="field">
              <label className="field-label">Notes</label>
              <input value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} placeholder="Optional note…" />
            </div>
          </div>
          <div className="drawer-footer">
            <button className="btn btn-primary" type="submit" disabled={submitting} style={{ flex: 1, justifyContent: 'center' }}>
              {submitting ? 'Recording…' : 'Record payment'}
            </button>
            <button className="btn btn-ghost" type="button" onClick={() => setDrawerOpen(false)}>Cancel</button>
          </div>
        </form>
      </div>
    </>
  )
}
