import { type FormEvent, useDeferredValue, useEffect, useState } from 'react'
import { apiFetch } from '../api'
import type { Member, MemberCreate } from '../types'
import { errorMessage, formatDate, formatRole } from '../utils'
import { SkeletonTableRows } from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const defaultForm: MemberCreate = {
  full_name: '',
  phone: '',
  email: '',
  gender: '',
  emergency_contact: '',
}

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
    } catch (error) {
      pushNotice('error', 'Failed to load members', errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchMembers()
  }, [accessToken, apiBaseUrl, branchId])

  const filtered = members.filter((member) => {
    if (filterStatus && member.status !== filterStatus) return false
    if (!deferredSearch) return true
    return `${member.full_name} ${member.phone} ${member.member_code} ${member.status}`.toLowerCase().includes(deferredSearch)
  })

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
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
    } catch (error) {
      pushNotice('error', 'Failed to create member', errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  function updateForm(key: keyof MemberCreate, value: string) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  const activeCount = members.filter((member) => member.status === 'active').length
  const pausedCount = members.filter((member) => member.status === 'paused').length
  const inactiveCount = members.filter((member) => ['inactive', 'expired'].includes(member.status)).length

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Roster control</div>
          <div className="page-title">Members</div>
          <div className="page-sub">
            Keep the active base clean, make lapse risk obvious, and give front-desk staff a fast roster lookup.
          </div>
        </div>

        <div className="page-actions">
          <span className="badge badge-active">{activeCount} active</span>
          <button className="btn btn-primary" type="button" onClick={() => setDrawerOpen(true)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add member
          </button>
        </div>
      </div>

      <div className="page-body">
        {!loading && (
          <div className="summary-row">
            <div className="summary-card animate-in delay-1">
              <div className="summary-label">Active members</div>
              <div className="summary-amount">{activeCount}</div>
              <div className="summary-note">Current paying members available for training and renewal.</div>
            </div>
            <div className="summary-card animate-in delay-2">
              <div className="summary-label">Paused profiles</div>
              <div className="summary-amount">{pausedCount}</div>
              <div className="summary-note">Members likely to return if staff follows up at the right time.</div>
            </div>
            <div className="summary-card animate-in delay-3">
              <div className="summary-label">At-risk accounts</div>
              <div className="summary-amount">{inactiveCount}</div>
              <div className="summary-note">Expired or inactive records that should not be ignored.</div>
            </div>
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
                placeholder="Search by member, code, or phone"
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
              {['active', 'expired', 'paused', 'inactive'].map((status) => (
                <option key={status} value={status}>
                  {formatRole(status)}
                </option>
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
                      <td className="mono">{member.member_code}</td>
                      <td>
                        <Badge status={member.status} />
                      </td>
                      <td className="mono">{member.phone}</td>
                      <td>{formatDate(member.joined_at || member.created_at)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="empty-row">
                      No members match this filter. Try a different status or create the next member profile.
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
          <span className="drawer-title">Add member</span>
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
              <label className="field-label" htmlFor="member-name">Full name</label>
              <input
                id="member-name"
                value={form.full_name}
                onChange={(event) => updateForm('full_name', event.target.value)}
                placeholder="Rhea Basnet"
                required
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="member-phone">Phone</label>
              <input
                id="member-phone"
                value={form.phone}
                onChange={(event) => updateForm('phone', event.target.value)}
                placeholder="+91 98214 30761"
                required
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="member-email">Email</label>
              <input
                id="member-email"
                type="email"
                value={form.email ?? ''}
                onChange={(event) => updateForm('email', event.target.value)}
                placeholder="rhea@example.com"
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="member-gender">Gender</label>
              <select
                id="member-gender"
                value={form.gender ?? ''}
                onChange={(event) => updateForm('gender', event.target.value)}
              >
                <option value="">Prefer not to say</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="field">
              <label className="field-label" htmlFor="member-emergency">Emergency contact</label>
              <input
                id="member-emergency"
                value={form.emergency_contact ?? ''}
                onChange={(event) => updateForm('emergency_contact', event.target.value)}
                placeholder="Kiran Basnet, +91 98111 27654"
              />
              <div className="field-hint">
                Keep this useful for the front desk and trainers who need a real fallback contact.
              </div>
            </div>
          </div>

          <div className="drawer-footer">
            <button className="btn btn-primary" type="submit" disabled={submitting} style={{ flex: 1 }}>
              {submitting ? 'Creating...' : 'Create member'}
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
