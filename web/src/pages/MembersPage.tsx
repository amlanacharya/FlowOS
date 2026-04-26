import { type FormEvent, useCallback, useDeferredValue, useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../api'
import type {
  Member,
  MemberCreate,
  MemberDetail,
  MemberUpdate,
  PlanOption,
  QrCheckinResponse,
} from '../types'
import { errorMessage, formatDate, formatRole } from '../utils'
import { SkeletonTableRows } from '../components/Skeleton'
import { QrScannerModal } from '../components/QrScannerModal'
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
  plan_id: '',
  email: '',
  aadhaar_no: '',
  pan_no: '',
  date_of_birth: '',
  gender: '',
  emergency_contact: '',
  notes: '',
  status: 'active',
}

type EditMemberForm = {
  full_name: string
  phone: string
  email: string
  aadhaar_no: string
  pan_no: string
  date_of_birth: string
  gender: string
  emergency_contact: string
  notes: string
  status: string
}

const defaultEditForm: EditMemberForm = {
  full_name: '',
  phone: '',
  email: '',
  aadhaar_no: '',
  pan_no: '',
  date_of_birth: '',
  gender: '',
  emergency_contact: '',
  notes: '',
  status: 'active',
}

function Badge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{formatRole(status)}</span>
}

export default function MembersPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [plans, setPlans] = useState<PlanOption[]>([])
  const [filterStatus, setFilterStatus] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [qrScannerOpen, setQrScannerOpen] = useState(false)
  const [form, setForm] = useState<MemberCreate>(defaultForm)
  const [submitting, setSubmitting] = useState(false)
  const [editDrawerOpen, setEditDrawerOpen] = useState(false)
  const [editingMemberId, setEditingMemberId] = useState('')
  const [editForm, setEditForm] = useState<EditMemberForm>(defaultEditForm)
  const [editLoading, setEditLoading] = useState(false)
  const [editSubmitting, setEditSubmitting] = useState(false)

  const deferredSearch = useDeferredValue(search.trim().toLowerCase())
  const query = useMemo(() => (branchId ? { branch_id: branchId } : undefined), [branchId])

  const fetchMembers = useCallback(async () => {
    try {
      const [membersData, plansData] = await Promise.all([
        apiFetch<Member[]>(apiBaseUrl, '/api/v1/members', { token: accessToken, query }),
        apiFetch<PlanOption[]>(apiBaseUrl, '/api/v1/plans', { token: accessToken, query }),
      ])
      setMembers(membersData)
      setPlans(plansData)
    } catch (error) {
      pushNotice('error', 'Failed to load members', errorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [accessToken, apiBaseUrl, pushNotice, query])

  useEffect(() => {
    void fetchMembers()
  }, [fetchMembers])

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

  function updateEditForm(key: keyof EditMemberForm, value: string) {
    setEditForm((current) => ({ ...current, [key]: value }))
  }

  async function openEditDrawer(memberId: string) {
    setEditLoading(true)
    try {
      const detail = await apiFetch<MemberDetail>(apiBaseUrl, `/api/v1/members/${memberId}`, {
        token: accessToken,
      })
      setEditingMemberId(memberId)
      setEditForm({
        full_name: detail.full_name ?? '',
        phone: detail.phone ?? '',
        email: detail.email ?? '',
        aadhaar_no: detail.aadhaar_no ?? '',
        pan_no: detail.pan_no ?? '',
        date_of_birth: detail.date_of_birth ?? '',
        gender: detail.gender ?? '',
        emergency_contact: detail.emergency_contact ?? '',
        notes: detail.notes ?? '',
        status: detail.status ?? 'active',
      })
      setEditDrawerOpen(true)
    } catch (error) {
      pushNotice('error', 'Failed to load member details', errorMessage(error))
    } finally {
      setEditLoading(false)
    }
  }

  async function handleEditSubmit(event: FormEvent) {
    event.preventDefault()
    if (!editingMemberId) {
      return
    }
    setEditSubmitting(true)

    const payload: MemberUpdate = {
      full_name: editForm.full_name,
      phone: editForm.phone,
      email: editForm.email || undefined,
      aadhaar_no: editForm.aadhaar_no || undefined,
      pan_no: editForm.pan_no || undefined,
      date_of_birth: editForm.date_of_birth || undefined,
      gender: editForm.gender || undefined,
      emergency_contact: editForm.emergency_contact || undefined,
      notes: editForm.notes || undefined,
      status: editForm.status || undefined,
    }

    try {
      await apiFetch<Member>(apiBaseUrl, `/api/v1/members/${editingMemberId}`, {
        method: 'PATCH',
        token: accessToken,
        body: payload,
      })
      setEditDrawerOpen(false)
      pushNotice('success', 'Member updated', `${editForm.full_name} profile updated successfully.`)
      setLoading(true)
      await fetchMembers()
    } catch (error) {
      pushNotice('error', 'Failed to update member', errorMessage(error))
    } finally {
      setEditSubmitting(false)
    }
  }

  function handleQrCheckinSuccess(result: QrCheckinResponse) {
    setQrScannerOpen(false)
    pushNotice('success', `${result.member_name} checked in successfully`, '')
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
          <button className="btn btn-secondary" type="button" onClick={() => setQrScannerOpen(true)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M3 4a1 1 0 0 1 1-1h6V1m10 3a1 1 0 0 0-1-1h-6v2m7 4v6h2V8m0 8v6h-2v-6M3 12v6h2v-6m12-8h6a1 1 0 0 1 1 1v6h2v-6a1 1 0 0 0-1-1h-6V4M3 8h2V4H4a1 1 0 0 0-1 1v3z" />
            </svg>
            Scan QR
          </button>
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
              {['active', 'inactive', 'terminated', 'blacklisted', 'expired', 'paused'].map((status) => (
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
                  <th>Actions</th>
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
                      <td>
                        <button
                          className="btn btn-ghost"
                          type="button"
                          onClick={() => void openEditDrawer(member.id)}
                          disabled={editLoading}
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="empty-row">
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
              <label className="field-label" htmlFor="member-plan">Membership plan</label>
              <select
                id="member-plan"
                value={form.plan_id}
                onChange={(event) => updateForm('plan_id', event.target.value)}
                required
              >
                <option value="">Select plan</option>
                {plans.map((plan) => (
                  <option key={plan.id} value={plan.id}>
                    {plan.name} ({plan.plan_type.replaceAll('_', ' ')}) - INR {plan.price}
                  </option>
                ))}
              </select>
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
              <label className="field-label" htmlFor="member-aadhaar">Aadhaar number</label>
              <input
                id="member-aadhaar"
                value={form.aadhaar_no ?? ''}
                onChange={(event) => updateForm('aadhaar_no', event.target.value)}
                placeholder="1234 5678 9012"
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="member-pan">PAN number</label>
              <input
                id="member-pan"
                value={form.pan_no ?? ''}
                onChange={(event) => updateForm('pan_no', event.target.value)}
                placeholder="ABCDE1234F"
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="member-dob">Date of birth</label>
              <input
                id="member-dob"
                type="date"
                value={form.date_of_birth ?? ''}
                onChange={(event) => updateForm('date_of_birth', event.target.value)}
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

            <div className="field">
              <label className="field-label" htmlFor="member-notes">Notes</label>
              <textarea
                id="member-notes"
                value={form.notes ?? ''}
                onChange={(event) => updateForm('notes', event.target.value)}
                placeholder="Initial joining notes"
              />
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

      <div className={`drawer-overlay ${editDrawerOpen ? 'open' : ''}`} onClick={() => setEditDrawerOpen(false)} />
      <div className={`drawer ${editDrawerOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <span className="drawer-title">Edit member</span>
          <button className="btn-icon" type="button" onClick={() => setEditDrawerOpen(false)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleEditSubmit} style={{ display: 'contents' }}>
          <div className="drawer-body">
            <div className="field">
              <label className="field-label" htmlFor="edit-member-name">Full name</label>
              <input
                id="edit-member-name"
                value={editForm.full_name}
                onChange={(event) => updateEditForm('full_name', event.target.value)}
                required
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="edit-member-phone">Phone</label>
              <input
                id="edit-member-phone"
                value={editForm.phone}
                onChange={(event) => updateEditForm('phone', event.target.value)}
                required
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="edit-member-email">Email</label>
              <input
                id="edit-member-email"
                type="email"
                value={editForm.email}
                onChange={(event) => updateEditForm('email', event.target.value)}
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="edit-member-aadhaar">Aadhaar number</label>
              <input
                id="edit-member-aadhaar"
                value={editForm.aadhaar_no}
                onChange={(event) => updateEditForm('aadhaar_no', event.target.value)}
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="edit-member-pan">PAN number</label>
              <input
                id="edit-member-pan"
                value={editForm.pan_no}
                onChange={(event) => updateEditForm('pan_no', event.target.value)}
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="edit-member-dob">Date of birth</label>
              <input
                id="edit-member-dob"
                type="date"
                value={editForm.date_of_birth}
                onChange={(event) => updateEditForm('date_of_birth', event.target.value)}
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="edit-member-status">Status</label>
              <select
                id="edit-member-status"
                value={editForm.status}
                onChange={(event) => updateEditForm('status', event.target.value)}
              >
                {['active', 'inactive', 'terminated', 'blacklisted', 'paused', 'expired'].map((status) => (
                  <option key={status} value={status}>
                    {formatRole(status)}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label className="field-label" htmlFor="edit-member-gender">Gender</label>
              <select
                id="edit-member-gender"
                value={editForm.gender}
                onChange={(event) => updateEditForm('gender', event.target.value)}
              >
                <option value="">Prefer not to say</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="field">
              <label className="field-label" htmlFor="edit-member-emergency">Emergency contact</label>
              <input
                id="edit-member-emergency"
                value={editForm.emergency_contact}
                onChange={(event) => updateEditForm('emergency_contact', event.target.value)}
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="edit-member-notes">Notes</label>
              <textarea
                id="edit-member-notes"
                value={editForm.notes}
                onChange={(event) => updateEditForm('notes', event.target.value)}
              />
            </div>
          </div>

          <div className="drawer-footer">
            <button className="btn btn-primary" type="submit" disabled={editSubmitting} style={{ flex: 1 }}>
              {editSubmitting ? 'Saving...' : 'Save changes'}
            </button>
            <button className="btn btn-ghost" type="button" onClick={() => setEditDrawerOpen(false)}>
              Cancel
            </button>
          </div>
        </form>
      </div>

      <QrScannerModal
        open={qrScannerOpen}
        onClose={() => setQrScannerOpen(false)}
        onSuccess={handleQrCheckinSuccess}
        apiBaseUrl={apiBaseUrl}
        accessToken={accessToken}
        branchId={branchId}
        pushNotice={pushNotice}
      />
    </>
  )
}
