import { type FormEvent, useState } from 'react'
import { apiFetch } from '../api'
import type { Branch, BranchCreate, Organization, OrganizationCreate, UserProfile } from '../types'
import { errorMessage } from '../utils'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  onApiBaseUrlChange: (url: string) => void
  accessToken: string
  profile: UserProfile | null
  branchOverride: string
  onBranchOverrideChange: (id: string) => void
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const defaultOrgForm: OrganizationCreate = {
  name: '',
  slug: '',
  owner_email: '',
  phone: '',
}

const defaultBranchForm: BranchCreate & { org_id: string } = {
  org_id: '',
  name: '',
  address: '',
  city: '',
  phone: '',
}

export default function SettingsPage({
  apiBaseUrl,
  onApiBaseUrlChange,
  accessToken,
  profile,
  branchOverride,
  onBranchOverrideChange,
  pushNotice,
}: Props) {
  const [orgForm, setOrgForm] = useState(defaultOrgForm)
  const [branchForm, setBranchForm] = useState(defaultBranchForm)
  const [createdOrg, setCreatedOrg] = useState<Organization | null>(null)
  const [createdBranch, setCreatedBranch] = useState<Branch | null>(null)
  const [busyOrg, setBusyOrg] = useState(false)
  const [busyBranch, setBusyBranch] = useState(false)

  async function handleOrgCreate(event: FormEvent) {
    event.preventDefault()
    setBusyOrg(true)

    try {
      const organization = await apiFetch<Organization>(apiBaseUrl, '/api/v1/organizations', {
        method: 'POST',
        body: orgForm,
      })

      setCreatedOrg(organization)
      setBranchForm((current) => ({ ...current, org_id: organization.id }))
      setOrgForm(defaultOrgForm)
      pushNotice('success', 'Organization created', `${organization.name} is ready.`)
    } catch (error) {
      pushNotice('error', 'Failed to create org', errorMessage(error))
    } finally {
      setBusyOrg(false)
    }
  }

  async function handleBranchCreate(event: FormEvent) {
    event.preventDefault()
    setBusyBranch(true)

    try {
      const branch = await apiFetch<Branch>(apiBaseUrl, '/api/v1/branches', {
        method: 'POST',
        token: accessToken,
        query: { org_id: branchForm.org_id },
        body: {
          name: branchForm.name,
          address: branchForm.address,
          city: branchForm.city,
          phone: branchForm.phone,
        },
      })

      setCreatedBranch(branch)
      onBranchOverrideChange(branch.id)
      setBranchForm((current) => ({ ...defaultBranchForm, org_id: current.org_id }))
      pushNotice('success', 'Branch created', `${branch.name} is now active.`)
    } catch (error) {
      pushNotice('error', 'Failed to create branch', errorMessage(error))
    } finally {
      setBusyBranch(false)
    }
  }

  const bootstrapSteps = [
    { label: 'Organization created', done: Boolean(createdOrg || profile?.org_id) },
    { label: 'Branch configured', done: Boolean(createdBranch || branchOverride || profile?.branch_id) },
    { label: 'Staff session active', done: Boolean(accessToken) },
  ]

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Workspace control</div>
          <div className="page-title">Settings</div>
          <div className="page-sub">
            Configure the backend connection, bootstrap new clubs, and verify which organization and branch the current
            session is operating against.
          </div>
        </div>

        <div className="page-actions">
          <span className="badge badge-active">{accessToken ? 'Session active' : 'No session'}</span>
          <span className="badge badge-new">{branchOverride ? 'Override enabled' : 'Profile branch'}</span>
        </div>
      </div>

      <div className="page-body">
        <div className="summary-row">
          <div className="summary-card animate-in delay-1">
            <div className="summary-label">Active staff session</div>
            <div className="summary-amount">{profile ? 'Live' : 'Idle'}</div>
            <div className="summary-note">
              {profile ? `${profile.full_name} is authenticated in this browser.` : 'Sign in to unlock branch setup actions.'}
            </div>
          </div>

          <div className="summary-card animate-in delay-2">
            <div className="summary-label">Organization context</div>
            <div className="summary-amount">{createdOrg?.name || (profile?.org_id ? 'Ready' : 'Pending')}</div>
            <div className="summary-note">Use this space to create a new club or confirm the current org scope.</div>
          </div>

          <div className="summary-card animate-in delay-3">
            <div className="summary-label">Branch resolution</div>
            <div className="summary-amount">{branchOverride ? 'Manual' : 'Profile'}</div>
            <div className="summary-note">Current branch source: {branchOverride || profile?.branch_id || 'not configured yet'}.</div>
          </div>
        </div>

        <div className="split-grid">
          <div className="card animate-in delay-2">
            <div className="card-header">
              <span className="card-title">Active session</span>
              <span className="card-meta">Identity and scope</span>
            </div>
            <div className="card-body">
              {profile ? (
                <>
                  <div className="info-row">
                    <span className="info-key">Name</span>
                    <span className="info-val">{profile.full_name}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-key">Email</span>
                    <span className="info-val">{profile.email}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-key">Role</span>
                    <span className="info-val">{profile.role.replaceAll('_', ' ')}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-key">Staff ID</span>
                    <span className="info-val">{profile.staff_id}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-key">Org ID</span>
                    <span className="info-val">{profile.org_id}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-key">Branch ID</span>
                    <span className="info-val">{profile.branch_id}</span>
                  </div>
                </>
              ) : (
                <div className="empty-row">No active session. Sign in first to inspect branch-scoped settings.</div>
              )}
            </div>
          </div>

          <div className="card animate-in delay-3">
            <div className="card-header">
              <span className="card-title">Bootstrap checklist</span>
              <span className="card-meta">Required setup order</span>
            </div>
            <div className="card-body">
              {bootstrapSteps.map((step) => (
                <div key={step.label} className="info-row">
                  <div>
                    <div className="table-name">{step.label}</div>
                    <div className="info-key">{step.done ? 'Complete' : 'Still needs action'}</div>
                  </div>
                  <span className={`badge ${step.done ? 'badge-active' : 'badge-inactive'}`}>
                    {step.done ? 'Done' : 'Open'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="split-grid">
          <div className="card animate-in delay-4">
            <div className="card-header">
              <span className="card-title">Connection and routing</span>
              <span className="card-meta">Frontend environment</span>
            </div>
            <div className="card-body">
              <div className="field">
                <label className="field-label" htmlFor="settings-api-base">API base URL</label>
                <input
                  id="settings-api-base"
                  value={apiBaseUrl}
                  onChange={(event) => onApiBaseUrlChange(event.target.value)}
                  placeholder="http://127.0.0.1:8000"
                />
              </div>

              <div className="field" style={{ marginTop: 18 }}>
                <label className="field-label" htmlFor="settings-branch-override">Branch ID override</label>
                <input
                  id="settings-branch-override"
                  value={branchOverride}
                  onChange={(event) => onBranchOverrideChange(event.target.value)}
                  placeholder="Paste a branch_id to force this workspace"
                />
                <div className="field-hint">
                  Leave this blank to use the authenticated user&apos;s branch. Set it only when staff needs to inspect a
                  different branch deliberately.
                </div>
              </div>

              {(createdOrg || createdBranch) && (
                <div style={{ marginTop: 18 }}>
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

          <form className="card animate-in delay-5" onSubmit={handleOrgCreate}>
            <div className="card-header">
              <span className="card-title">Create organization</span>
              <span className="card-meta">Public endpoint</span>
            </div>
            <div className="card-body">
              <div className="field">
                <label className="field-label" htmlFor="org-name">Gym name</label>
                <input
                  id="org-name"
                  value={orgForm.name}
                  onChange={(event) => setOrgForm((current) => ({ ...current, name: event.target.value }))}
                  placeholder="Northline Strength Club"
                  required
                />
              </div>

              <div className="field" style={{ marginTop: 18 }}>
                <label className="field-label" htmlFor="org-slug">Slug</label>
                <input
                  id="org-slug"
                  value={orgForm.slug}
                  onChange={(event) => setOrgForm((current) => ({ ...current, slug: event.target.value }))}
                  placeholder="northline-strength-club"
                  required
                />
              </div>

              <div className="field" style={{ marginTop: 18 }}>
                <label className="field-label" htmlFor="org-owner-email">Owner email</label>
                <input
                  id="org-owner-email"
                  type="email"
                  value={orgForm.owner_email}
                  onChange={(event) => setOrgForm((current) => ({ ...current, owner_email: event.target.value }))}
                  placeholder="owner@northline.club"
                  required
                />
              </div>

              <div className="field" style={{ marginTop: 18 }}>
                <label className="field-label" htmlFor="org-phone">Phone</label>
                <input
                  id="org-phone"
                  value={orgForm.phone ?? ''}
                  onChange={(event) => setOrgForm((current) => ({ ...current, phone: event.target.value }))}
                  placeholder="+91 99220 48133"
                />
              </div>

              <button className="btn btn-primary" type="submit" disabled={busyOrg} style={{ marginTop: 20 }}>
                {busyOrg ? 'Creating...' : 'Create organization'}
              </button>
            </div>
          </form>
        </div>

        <form className="card animate-in delay-6" onSubmit={handleBranchCreate}>
          <div className="card-header">
            <span className="card-title">Create branch</span>
            <span className="card-meta">Requires active session</span>
          </div>
          <div className="card-body">
            <div className="split-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
              <div>
                <div className="field">
                  <label className="field-label" htmlFor="branch-org-id">Organization ID</label>
                  <input
                    id="branch-org-id"
                    value={branchForm.org_id}
                    onChange={(event) => setBranchForm((current) => ({ ...current, org_id: event.target.value }))}
                    placeholder="From created org or existing profile"
                    required
                  />
                </div>

                <div className="field" style={{ marginTop: 18 }}>
                  <label className="field-label" htmlFor="branch-name">Branch name</label>
                  <input
                    id="branch-name"
                    value={branchForm.name}
                    onChange={(event) => setBranchForm((current) => ({ ...current, name: event.target.value }))}
                    placeholder="Downtown Performance Lab"
                    required
                  />
                </div>

                <div className="field" style={{ marginTop: 18 }}>
                  <label className="field-label" htmlFor="branch-city">City</label>
                  <input
                    id="branch-city"
                    value={branchForm.city ?? ''}
                    onChange={(event) => setBranchForm((current) => ({ ...current, city: event.target.value }))}
                    placeholder="Bengaluru"
                  />
                </div>
              </div>

              <div>
                <div className="field">
                  <label className="field-label" htmlFor="branch-address">Address</label>
                  <input
                    id="branch-address"
                    value={branchForm.address ?? ''}
                    onChange={(event) => setBranchForm((current) => ({ ...current, address: event.target.value }))}
                    placeholder="3rd floor, Cunningham Road"
                  />
                </div>

                <div className="field" style={{ marginTop: 18 }}>
                  <label className="field-label" htmlFor="branch-phone">Phone</label>
                  <input
                    id="branch-phone"
                    value={branchForm.phone ?? ''}
                    onChange={(event) => setBranchForm((current) => ({ ...current, phone: event.target.value }))}
                    placeholder="+91 98452 11076"
                  />
                </div>

                <div className="field-hint" style={{ marginTop: 18 }}>
                  Once the branch is created, this screen automatically sets the new branch override for the current
                  browser session.
                </div>
              </div>
            </div>

            <button className="btn btn-primary" type="submit" disabled={busyBranch || !accessToken} style={{ marginTop: 20 }}>
              {busyBranch ? 'Opening...' : 'Open branch'}
            </button>
          </div>
        </form>
      </div>
    </>
  )
}
