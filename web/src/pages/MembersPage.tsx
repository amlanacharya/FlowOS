import { type FormEvent, useEffect, useDeferredValue, useState } from 'react'
import { apiFetch } from '../api'
import type { Member, MemberCreate } from '../types'
import { formatDate, formatRole, errorMessage } from '../utils'
import { SkeletonTableRows } from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const defaultForm: MemberCreate = { full_name: '', phone: '', email: '', gender: '', emergency_contact: '' }

function Badge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{formatRole(status)}</span>
}

export default function MembersPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [form, setForm] = useState<MemberCreate>(defaultForm)
  const [submitting, setSubmitting] = useState(false)

  const deferredSearch = useDeferredValue(search.trim().toLowerCase())
  const query = branchId ? { branch_id: branchId } : undefined

  async function fetchMembers() {
    try {
      const data = await apiFetch<Member[]>(apiBaseUrl, '/api/v1/members', { token: accessToken, query })
      setMembers(data)
    } catch (err) {
      pushNotice('error', 'Failed to load members', errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void fetchMembers() }, [apiBaseUrl, accessToken, branchId])

  const filtered = members.filter((m) => {
    if (filterStatus && m.status !== filterStatus) return false
    if (!deferredSearch) return true
    return `${m.full_name} ${m.phone} ${m.member_code} ${m.status}`.toLowerCase().includes(deferredSearch)
  })

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      await apiFetch<Member>(apiBaseUrl, '/api/v1/members', {
        method: 'POST',
        token: accessToken,
        query,
        body: form,
      })
      setForm(defaultForm)
      setDrawerOpen(false)
      pushNotice('success', 'Member created', `${form.full_name} has been added to the roster.`)
      setLoading(true)
      await fetchMembers()
    } catch (err) {
      pushNotice('error', 'Failed to create member', errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  function updateForm(key: keyof MemberCreate, value: string) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  const activeCount = members.filter((m) => m.status === 'active').length

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">MEMBERS</div>
          <div className="page-sub">{activeCount} active · {members.length} total members on roster</div>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" type="button" onClick={() => setDrawerOpen(true)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add member
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
                placeholder="Search by name, code, phone…"
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
              {['active', 'expired', 'paused', 'inactive'].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>

            <span className="table-count">{filtered.length} members</span>
          </div>

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Member</th>
                  <th>Code</th>
                  <th>Status</th>
                  <th>Phone</th>
                  <th>Joined</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <SkeletonTableRows count={6} />
                ) : filtered.length > 0 ? (
                  filtered.map((member) => (
                    <tr key={member.id}>
                      <td>
                        <div className="table-name">{member.full_name}</div>
                        {member.branch_id && <div className="table-sub">Branch: {member.branch_id.slice(0, 8)}</div>}
                      </td>
                      <td style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-lo)' }}>{member.member_code}</td>
                      <td><Badge status={member.status} /></td>
                      <td style={{ color: 'var(--text-mid)', fontFamily: 'monospace', fontSize: 13 }}>{member.phone}</td>
                      <td style={{ color: 'var(--text-lo)' }}>{formatDate(member.joined_at || member.created_at)}</td>
                    </tr>
                  ))
                ) : (
                  <tr><td colSpan={5} className="empty-row">No members found. Create your first member profile.</td></tr>
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
          <span className="drawer-title">ADD MEMBER</span>
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
              <input value={form.full_name} onChange={(e) => updateForm('full_name', e.target.value)} placeholder="Riya Basnet" required />
            </div>
            <div className="field">
              <label className="field-label">Phone *</label>
              <input value={form.phone} onChange={(e) => updateForm('phone', e.target.value)} placeholder="98xxxxxxxx" required />
            </div>
            <div className="field">
              <label className="field-label">Email</label>
              <input type="email" value={form.email ?? ''} onChange={(e) => updateForm('email', e.target.value)} placeholder="member@example.com" />
            </div>
            <div className="field">
              <label className="field-label">Gender</label>
              <select value={form.gender ?? ''} onChange={(e) => updateForm('gender', e.target.value)}>
                <option value="">Prefer not to say</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="field">
              <label className="field-label">Emergency contact</label>
              <input value={form.emergency_contact ?? ''} onChange={(e) => updateForm('emergency_contact', e.target.value)} placeholder="Name and phone" />
            </div>
          </div>
          <div className="drawer-footer">
            <button className="btn btn-primary" type="submit" disabled={submitting} style={{ flex: 1, justifyContent: 'center' }}>
              {submitting ? 'Creating…' : 'Create member'}
            </button>
            <button className="btn btn-ghost" type="button" onClick={() => setDrawerOpen(false)}>Cancel</button>
          </div>
        </form>
      </div>
    </>
  )
}
