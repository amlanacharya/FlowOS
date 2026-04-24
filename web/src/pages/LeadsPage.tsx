import { type FormEvent, useDeferredValue, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { Lead, LeadCreate } from '../types'
import { errorMessage, formatDate, formatRole } from '../utils'
import { SkeletonTableRows } from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const defaultForm: LeadCreate = {
  full_name: '',
  phone: '',
  email: '',
  source: '',
  notes: '',
}

const statusOrder = ['new', 'contacted', 'trial_scheduled', 'trial_attended', 'converted', 'lost']

function Badge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{formatRole(status)}</span>
}

export default function LeadsPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [form, setForm] = useState<LeadCreate>(defaultForm)
  const [submitting, setSubmitting] = useState(false)

  const deferredSearch = useDeferredValue(search.trim().toLowerCase())
  const query = branchId ? { branch_id: branchId } : undefined

  async function fetchLeads() {
    try {
      const data = await apiFetch<Lead[]>(apiBaseUrl, '/api/v1/leads', { token: accessToken, query })
      setLeads(data)
    } catch (error) {
      pushNotice('error', 'Failed to load leads', errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchLeads()
  }, [accessToken, apiBaseUrl, branchId])

  const filtered = leads.filter((lead) => {
    if (filterStatus && lead.status !== filterStatus) return false
    if (!deferredSearch) return true
    return `${lead.full_name} ${lead.phone} ${lead.status}`.toLowerCase().includes(deferredSearch)
  })

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)

    try {
      await apiFetch<Lead>(apiBaseUrl, '/api/v1/leads', {
        method: 'POST',
        token: accessToken,
        query,
        body: form,
      })

      setForm(defaultForm)
      setDrawerOpen(false)
      pushNotice('success', 'Lead added', `${form.full_name} entered the pipeline.`)
      setLoading(true)
      await fetchLeads()
    } catch (error) {
      pushNotice('error', 'Failed to create lead', errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  function updateForm(key: keyof LeadCreate, value: string) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  const leadSummary = [
    {
      label: 'New this cycle',
      value: leads.filter((lead) => lead.status === 'new').length,
      note: 'Fresh inquiries waiting for first contact.',
    },
    {
      label: 'Trials in motion',
      value: leads.filter((lead) => ['trial_scheduled', 'trial_attended'].includes(lead.status)).length,
      note: 'Leads closest to conversion right now.',
    },
    {
      label: 'Converted',
      value: leads.filter((lead) => lead.status === 'converted').length,
      note: 'People already moved into the member base.',
    },
  ]

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Growth desk</div>
          <div className="page-title">Leads</div>
          <div className="page-sub">
            Keep the funnel tight, move hot prospects quickly, and make the next action obvious for staff on shift.
          </div>
        </div>

        <div className="page-actions">
          <span className="badge badge-new">{filtered.length} visible</span>
          <button className="btn btn-primary" type="button" onClick={() => setDrawerOpen(true)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add lead
          </button>
        </div>
      </div>

      <div className="page-body">
        {!loading && (
          <div className="summary-row">
            {leadSummary.map((item, index) => (
              <div key={item.label} className={`summary-card animate-in delay-${index + 1}`}>
                <div className="summary-label">{item.label}</div>
                <div className="summary-amount">{item.value}</div>
                <div className="summary-note">{item.note}</div>
              </div>
            ))}
          </div>
        )}

        <div className="card animate-in delay-2">
          <div className="table-toolbar">
            <div className="search-wrap">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                className="search-input"
                placeholder="Search by name, phone, or status"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>

            <select
              className="toolbar-select"
              value={filterStatus}
              onChange={(event) => setFilterStatus(event.target.value)}
            >
              <option value="">All statuses</option>
              {statusOrder.map((status) => (
                <option key={status} value={status}>
                  {formatRole(status)}
                </option>
              ))}
            </select>

            <span className="table-count">{filtered.length} leads</span>
          </div>

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Phone</th>
                  <th>Status</th>
                  <th>Source</th>
                  <th>Trial date</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <SkeletonTableRows count={6} />
                ) : filtered.length > 0 ? (
                  filtered.map((lead) => (
                    <tr key={lead.id}>
                      <td>
                        <div className="table-name">{lead.full_name}</div>
                      </td>
                      <td className="mono">{lead.phone}</td>
                      <td>
                        <Badge status={lead.status} />
                      </td>
                      <td>{lead.source || '-'}</td>
                      <td>{formatDate(lead.trial_scheduled_at)}</td>
                      <td>{formatDate(lead.created_at)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="empty-row">
                      No leads match this filter. Clear the search or add a new lead to restart the queue.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className={`drawer-overlay ${drawerOpen ? 'open' : ''}`} onClick={() => setDrawerOpen(false)} />
      <div className={`drawer ${drawerOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <span className="drawer-title">Add lead</span>
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
              <label className="field-label" htmlFor="lead-name">Full name</label>
              <input
                id="lead-name"
                value={form.full_name}
                onChange={(event) => updateForm('full_name', event.target.value)}
                placeholder="Aarav Khatri"
                required
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="lead-phone">Phone</label>
              <input
                id="lead-phone"
                value={form.phone}
                onChange={(event) => updateForm('phone', event.target.value)}
                placeholder="+91 98765 43120"
                required
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="lead-email">Email</label>
              <input
                id="lead-email"
                type="email"
                value={form.email ?? ''}
                onChange={(event) => updateForm('email', event.target.value)}
                placeholder="aarav@example.com"
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="lead-source">Source</label>
              <input
                id="lead-source"
                value={form.source ?? ''}
                onChange={(event) => updateForm('source', event.target.value)}
                placeholder="Referral, walk-in, Instagram"
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="lead-notes">Notes</label>
              <textarea
                id="lead-notes"
                value={form.notes ?? ''}
                onChange={(event) => updateForm('notes', event.target.value)}
                placeholder="Preferred training time, injury notes, pricing objections"
              />
              <div className="field-hint">
                Keep the next salesperson informed with concrete context instead of generic notes.
              </div>
            </div>
          </div>

          <div className="drawer-footer">
            <button className="btn btn-primary" type="submit" disabled={submitting} style={{ flex: 1 }}>
              {submitting ? 'Adding...' : 'Add to funnel'}
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
