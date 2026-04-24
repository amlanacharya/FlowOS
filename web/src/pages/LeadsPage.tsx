import { type FormEvent, useEffect, useDeferredValue, useState } from 'react'
import { apiFetch } from '../api'
import type { Lead, LeadCreate } from '../types'
import { formatDate, formatRole, errorMessage } from '../utils'
import { SkeletonTableRows } from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const defaultForm: LeadCreate = { full_name: '', phone: '', email: '', source: '', notes: '' }

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
    } catch (err) {
      pushNotice('error', 'Failed to load leads', errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void fetchLeads() }, [apiBaseUrl, accessToken, branchId])

  const filtered = leads.filter((l) => {
    if (filterStatus && l.status !== filterStatus) return false
    if (!deferredSearch) return true
    return `${l.full_name} ${l.phone} ${l.status}`.toLowerCase().includes(deferredSearch)
  })

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
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
      pushNotice('success', 'Lead added', `${form.full_name} entered the funnel.`)
      setLoading(true)
      await fetchLeads()
    } catch (err) {
      pushNotice('error', 'Failed to create lead', errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  function updateForm(key: keyof LeadCreate, value: string) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">LEADS</div>
          <div className="page-sub">{leads.length} total leads in the funnel</div>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" type="button" onClick={() => setDrawerOpen(true)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add lead
          </button>
        </div>
      </div>

      <div className="page-body">
        <div className="card animate-in">
          <div className="table-toolbar">
            <div className="search-wrap">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input
                className="search-input"
                placeholder="Search by name, phone, status…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-hi)', padding: '7px 10px', fontSize: 13, outline: 'none', fontFamily: 'var(--font-body)' }}
            >
              <option value="">All statuses</option>
              {statusOrder.map((s) => (
                <option key={s} value={s}>{formatRole(s)}</option>
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
                      <td><div className="table-name">{lead.full_name}</div></td>
                      <td style={{ color: 'var(--text-mid)', fontFamily: 'monospace', fontSize: 13 }}>{lead.phone}</td>
                      <td><Badge status={lead.status} /></td>
                      <td style={{ color: 'var(--text-lo)' }}>{(lead as unknown as { source?: string }).source || '—'}</td>
                      <td style={{ color: 'var(--text-lo)' }}>{formatDate(lead.trial_scheduled_at)}</td>
                      <td style={{ color: 'var(--text-lo)' }}>{formatDate(lead.created_at)}</td>
                    </tr>
                  ))
                ) : (
                  <tr><td colSpan={6} className="empty-row">No leads found. Add your first lead to get started.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Drawer */}
      <div className={`drawer-overlay ${drawerOpen ? 'open' : ''}`} onClick={() => setDrawerOpen(false)} />
      <div className={`drawer ${drawerOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <span className="drawer-title">ADD LEAD</span>
          <button className="btn-icon" type="button" onClick={() => setDrawerOpen(false)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <form onSubmit={handleSubmit} style={{ display: 'contents' }}>
          <div className="drawer-body">
            <div className="field">
              <label className="field-label">Full name *</label>
              <input value={form.full_name} onChange={(e) => updateForm('full_name', e.target.value)} placeholder="Aarya Shrestha" required />
            </div>
            <div className="field">
              <label className="field-label">Phone *</label>
              <input value={form.phone} onChange={(e) => updateForm('phone', e.target.value)} placeholder="98xxxxxxxx" required />
            </div>
            <div className="field">
              <label className="field-label">Email</label>
              <input type="email" value={form.email ?? ''} onChange={(e) => updateForm('email', e.target.value)} placeholder="lead@example.com" />
            </div>
            <div className="field">
              <label className="field-label">Source</label>
              <input value={form.source ?? ''} onChange={(e) => updateForm('source', e.target.value)} placeholder="Instagram, referral, walk-in…" />
            </div>
            <div className="field">
              <label className="field-label">Notes</label>
              <textarea value={form.notes ?? ''} onChange={(e) => updateForm('notes', e.target.value)} placeholder="Any additional context…" />
            </div>
          </div>
          <div className="drawer-footer">
            <button className="btn btn-primary" type="submit" disabled={submitting} style={{ flex: 1, justifyContent: 'center' }}>
              {submitting ? 'Adding…' : 'Add to funnel'}
            </button>
            <button className="btn btn-ghost" type="button" onClick={() => setDrawerOpen(false)}>Cancel</button>
          </div>
        </form>
      </div>
    </>
  )
}
