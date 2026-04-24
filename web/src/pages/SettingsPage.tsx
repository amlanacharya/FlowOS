import { type FormEvent, useState } from 'react'
import { apiFetch } from '../api'
import type { Branch, BranchCreate, Organization, OrganizationCreate } from '../types'
import { errorMessage } from '../utils'
import type { Notice } from '../components/NoticeStack'
import type { UserProfile } from '../types'

type Props = {
  apiBaseUrl: string
  onApiBaseUrlChange: (url: string) => void
  accessToken: string
  profile: UserProfile | null
  branchOverride: string
  onBranchOverrideChange: (id: string) => void
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const defaultOrgForm: OrganizationCreate = { name: '', slug: '', owner_email: '', phone: '' }
const defaultBranchForm: BranchCreate & { org_id: string } = { org_id: '', name: '', address: '', city: '', phone: '' }

export default function SettingsPage({
  apiBaseUrl, onApiBaseUrlChange, accessToken, profile, branchOverride, onBranchOverrideChange, pushNotice,
}: Props) {
  const [orgForm, setOrgForm] = useState(defaultOrgForm)
  const [branchForm, setBranchForm] = useState(defaultBranchForm)
  const [createdOrg, setCreatedOrg] = useState<Organization | null>(null)
  const [createdBranch, setCreatedBranch] = useState<Branch | null>(null)
  const [busyOrg, setBusyOrg] = useState(false)
  const [busyBranch, setBusyBranch] = useState(false)

  async function handleOrgCreate(e: FormEvent) {
    e.preventDefault()
    setBusyOrg(true)
    try {
      const org = await apiFetch<Organization>(apiBaseUrl, '/api/v1/organizations', {
        method: 'POST',
        body: orgForm,
      })
      setCreatedOrg(org)
      setBranchForm((f) => ({ ...f, org_id: org.id }))
      setOrgForm(defaultOrgForm)
      pushNotice('success', 'Organization created', `${org.name} is ready.`)
    } catch (err) {
      pushNotice('error', 'Failed to create org', errorMessage(err))
    } finally {
      setBusyOrg(false)
    }
  }

  async function handleBranchCreate(e: FormEvent) {
    e.preventDefault()
    setBusyBranch(true)
    try {
      const branch = await apiFetch<Branch>(apiBaseUrl, '/api/v1/branches', {
        method: 'POST',
        token: accessToken,
        query: { org_id: branchForm.org_id },
        body: { name: branchForm.name, address: branchForm.address, city: branchForm.city, phone: branchForm.phone },
      })
      setCreatedBranch(branch)
      onBranchOverrideChange(branch.id)
      setBranchForm((f) => ({ ...defaultBranchForm, org_id: f.org_id }))
      pushNotice('success', 'Branch created', `${branch.name} is now active.`)
    } catch (err) {
      pushNotice('error', 'Failed to create branch', errorMessage(err))
    } finally {
      setBusyBranch(false)
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">SETTINGS</div>
          <div className="page-sub">Session, organization, and branch configuration</div>
        </div>
      </div>

      <div className="page-body">
        {/* Session info */}
        <div className="card animate-in">
          <div className="card-header">
            <span className="card-title">Active session</span>
          </div>
          <div className="card-body">
            {profile ? (
              <div>
                {[
                  { key: 'Name', val: profile.full_name },
                  { key: 'Email', val: profile.email },
                  { key: 'Role', val: profile.role.replaceAll('_', ' ') },
                  { key: 'Staff ID', val: profile.staff_id },
                  { key: 'Org ID', val: profile.org_id },
                  { key: 'Branch ID', val: profile.branch_id },
                ].map((row) => (
                  <div key={row.key} className="info-row">
                    <span className="info-key">{row.key}</span>
                    <span className="info-val">{row.val}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: 'var(--text-lo)', fontSize: 13 }}>No active session.</div>
            )}
          </div>
        </div>

        {/* API + Branch */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div className="card animate-in delay-2">
            <div className="card-header"><span className="card-title">API connection</span></div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="field">
                <label className="field-label">API base URL</label>
                <input value={apiBaseUrl} onChange={(e) => onApiBaseUrlChange(e.target.value)} placeholder="http://localhost:8000" />
              </div>
              <div className="field">
                <label className="field-label">Branch ID override</label>
                <input value={branchOverride} onChange={(e) => onBranchOverrideChange(e.target.value)} placeholder="Paste a branch_id to override" />
              </div>
              {(createdOrg || createdBranch) && (
                <div style={{ marginTop: 4 }}>
                  {createdOrg && (
                    <div className="info-row">
                      <span className="info-key">Created org</span>
                      <span className="info-val">{createdOrg.name}</span>
                    </div>
                  )}
                  {createdBranch && (
                    <div className="info-row">
                      <span className="info-key">Created branch</span>
                      <span className="info-val">{createdBranch.name}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Bootstrap step indicator */}
          <div className="card animate-in delay-3">
            <div className="card-header"><span className="card-title">Bootstrap status</span></div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { step: 1, label: 'Organization created', done: Boolean(createdOrg || profile?.org_id) },
                { step: 2, label: 'Branch configured',    done: Boolean(createdBranch || branchOverride || profile?.branch_id) },
                { step: 3, label: 'Staff session active', done: Boolean(accessToken) },
              ].map(({ step, label, done }) => (
                <div key={step} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{
                    width: 22, height: 22, borderRadius: '50%',
                    background: done ? 'var(--success-dim)' : 'var(--surface-3)',
                    border: `1px solid ${done ? 'var(--success)' : 'var(--border)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  }}>
                    {done ? (
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="3">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      <span style={{ fontSize: 10, color: 'var(--text-lo)', fontWeight: 700 }}>{step}</span>
                    )}
                  </div>
                  <span style={{ fontSize: 13, color: done ? 'var(--text-hi)' : 'var(--text-lo)' }}>{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {/* Create Org */}
          <form className="card animate-in delay-4" onSubmit={handleOrgCreate}>
            <div className="card-header">
              <span className="card-title">Create organization</span>
              <span style={{ fontSize: 11, color: 'var(--text-lo)' }}>Public endpoint — no auth needed</span>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="field">
                <label className="field-label">Gym name *</label>
                <input value={orgForm.name} onChange={(e) => setOrgForm((f) => ({ ...f, name: e.target.value }))} placeholder="Northline Gym" required />
              </div>
              <div className="field">
                <label className="field-label">Slug *</label>
                <input value={orgForm.slug} onChange={(e) => setOrgForm((f) => ({ ...f, slug: e.target.value }))} placeholder="northline-gym" required />
              </div>
              <div className="field">
                <label className="field-label">Owner email *</label>
                <input type="email" value={orgForm.owner_email} onChange={(e) => setOrgForm((f) => ({ ...f, owner_email: e.target.value }))} placeholder="owner@gym.com" required />
              </div>
              <div className="field">
                <label className="field-label">Phone</label>
                <input value={orgForm.phone ?? ''} onChange={(e) => setOrgForm((f) => ({ ...f, phone: e.target.value }))} placeholder="+91 98xxxxxxxx" />
              </div>
              <button className="btn btn-primary" type="submit" disabled={busyOrg}>{busyOrg ? 'Creating…' : 'Create organization'}</button>
            </div>
          </form>

          {/* Create Branch */}
          <form className="card animate-in delay-5" onSubmit={handleBranchCreate}>
            <div className="card-header">
              <span className="card-title">Create branch</span>
              <span style={{ fontSize: 11, color: 'var(--text-lo)' }}>Requires active session</span>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="field">
                <label className="field-label">Organization ID *</label>
                <input value={branchForm.org_id} onChange={(e) => setBranchForm((f) => ({ ...f, org_id: e.target.value }))} placeholder="From created org or profile.org_id" required />
              </div>
              <div className="field">
                <label className="field-label">Branch name *</label>
                <input value={branchForm.name} onChange={(e) => setBranchForm((f) => ({ ...f, name: e.target.value }))} placeholder="Downtown Performance Lab" required />
              </div>
              <div className="field">
                <label className="field-label">City</label>
                <input value={branchForm.city ?? ''} onChange={(e) => setBranchForm((f) => ({ ...f, city: e.target.value }))} placeholder="Kathmandu" />
              </div>
              <div className="field">
                <label className="field-label">Address</label>
                <input value={branchForm.address ?? ''} onChange={(e) => setBranchForm((f) => ({ ...f, address: e.target.value }))} placeholder="3rd floor, main road" />
              </div>
              <button className="btn btn-primary" type="submit" disabled={busyBranch || !accessToken}>{busyBranch ? 'Opening…' : 'Open branch'}</button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
