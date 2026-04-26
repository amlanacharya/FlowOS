import { useEffect, useMemo, useState } from 'react'
import { apiFetch, listInvoices } from '../api'
import type { InvoiceItem, Member } from '../types'
import { errorMessage, formatCurrency, formatDate, formatRole } from '../utils'
import Skeleton from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

export default function InvoicesPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [loading, setLoading] = useState(true)
  const [invoices, setInvoices] = useState<InvoiceItem[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [invoiceNo, setInvoiceNo] = useState('')
  const [status, setStatus] = useState('')
  const [memberId, setMemberId] = useState('')
  const [memberSearch, setMemberSearch] = useState('')
  const [onlyOutstanding, setOnlyOutstanding] = useState(false)

  const filteredMembers = useMemo(() => {
    const q = memberSearch.trim().toLowerCase()
    if (!q) return members.slice(0, 60)
    return members
      .filter((member) => `${member.full_name} ${member.phone}`.toLowerCase().includes(q))
      .slice(0, 60)
  }, [memberSearch, members])

  const membersById = useMemo(
    () => new Map(members.map((member) => [member.id, `${member.full_name} (${member.phone})`])),
    [members],
  )

  async function fetchData() {
    setLoading(true)
    const [invoiceResult, memberResult] = await Promise.allSettled([
      listInvoices(apiBaseUrl, accessToken, branchId, {
        member_id: memberId || undefined,
        invoice_no: invoiceNo || undefined,
        status: status || undefined,
        only_outstanding: onlyOutstanding || undefined,
      }),
      apiFetch<Member[]>(apiBaseUrl, '/api/v1/members', { token: accessToken, query: { branch_id: branchId } }),
    ])

    if (invoiceResult.status === 'fulfilled') {
      setInvoices(invoiceResult.value)
    } else {
      pushNotice('error', 'Failed to load invoices', errorMessage(invoiceResult.reason))
    }

    if (memberResult.status === 'fulfilled') {
      setMembers(memberResult.value)
    } else {
      pushNotice('error', 'Failed to load members', errorMessage(memberResult.reason))
    }
    setLoading(false)
  }

  useEffect(() => {
    void fetchData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiBaseUrl, accessToken, branchId])

  async function applyFilters() {
    await fetchData()
  }

  const totalDue = invoices.reduce((sum, row) => sum + Number(row.amount_due), 0)
  const totalCount = invoices.length

  return (
    <div className="page-body">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Billing records</div>
          <div className="page-title">Invoices</div>
          <div className="page-sub">Track issued invoices, due balance, and payment status with operational filters.</div>
        </div>
        <div className="page-actions">
          <span className="badge badge-active">{totalCount} invoices</span>
          <span className="badge badge-warning">{formatCurrency(totalDue)} due</span>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="split-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <div className="field">
              <label className="field-label" htmlFor="invoice-no-filter">Invoice no</label>
              <input
                id="invoice-no-filter"
                value={invoiceNo}
                onChange={(event) => setInvoiceNo(event.target.value)}
                placeholder="INV-XXXXXX-1001"
              />
            </div>
            <div className="field">
              <label className="field-label" htmlFor="invoice-status-filter">Status</label>
              <select id="invoice-status-filter" value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="">All statuses</option>
                {['issued', 'partial', 'paid', 'overdue', 'void'].map((value) => (
                  <option key={value} value={value}>
                    {formatRole(value)}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field-label" htmlFor="invoice-member-search">Member phone/name search</label>
              <input
                id="invoice-member-search"
                value={memberSearch}
                onChange={(event) => setMemberSearch(event.target.value)}
                placeholder="Type member name or phone"
              />
            </div>
            <div className="field">
              <label className="field-label" htmlFor="invoice-member-select">Member</label>
              <select id="invoice-member-select" value={memberId} onChange={(event) => setMemberId(event.target.value)}>
                <option value="">All members</option>
                {filteredMembers.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.full_name} ({member.phone})
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={onlyOutstanding}
                onChange={(event) => setOnlyOutstanding(event.target.checked)}
              />
              Only outstanding invoices
            </label>
            <button className="btn btn-primary" type="button" onClick={() => void applyFilters()}>
              Apply filters
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Invoice list</span>
          <span className="card-meta">{invoices.length} records</span>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Member</th>
                <th>Type</th>
                <th>Status</th>
                <th>Total</th>
                <th>Paid</th>
                <th>Due</th>
                <th>Due date</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 6 }).map((_, index) => (
                  <tr key={index}>
                    <td colSpan={8} style={{ padding: '12px 14px' }}>
                      <Skeleton variant="text" />
                    </td>
                  </tr>
                ))
              ) : invoices.length ? (
                invoices.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <div className="table-name mono">{row.invoice_no}</div>
                      <div className="table-sub">{formatDate(row.created_at)}</div>
                    </td>
                    <td>{membersById.get(row.member_id) ?? row.member_id.slice(0, 8)}</td>
                    <td>{formatRole(row.invoice_type)}</td>
                    <td>
                      <span className="badge badge-active">{formatRole(row.status)}</span>
                    </td>
                    <td>{formatCurrency(Number(row.total_amount))}</td>
                    <td>{formatCurrency(Number(row.amount_paid))}</td>
                    <td className="text-error">{formatCurrency(Number(row.amount_due))}</td>
                    <td>{formatDate(row.due_date)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="empty-row">
                    No invoices found for selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
