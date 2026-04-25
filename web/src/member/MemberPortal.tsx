import { useEffect, useState } from 'react'
import { apiFetch, listWorkouts } from '../api'
import type { Member, WorkoutLog } from '../types'
import { formatDate } from '../utils'

const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'

export default function MemberPortal() {
  const [apiBaseUrl, setApiBaseUrl] = useState(() => localStorage.getItem('flowos-member-api-base') || DEFAULT_API_BASE_URL)
  const [token, setToken] = useState(() => localStorage.getItem('flowos-member-token') || '')
  const [branchId, setBranchId] = useState(() => localStorage.getItem('flowos-member-branch-id') || '')
  const [memberId, setMemberId] = useState(() => localStorage.getItem('flowos-member-id') || '')
  const [member, setMember] = useState<Member | null>(null)
  const [workouts, setWorkouts] = useState<WorkoutLog[]>([])
  const [message, setMessage] = useState('')

  useEffect(() => {
    localStorage.setItem('flowos-member-api-base', apiBaseUrl)
    localStorage.setItem('flowos-member-token', token)
    localStorage.setItem('flowos-member-branch-id', branchId)
    localStorage.setItem('flowos-member-id', memberId)
  }, [apiBaseUrl, branchId, memberId, token])

  async function loadPortal() {
    if (!token || !branchId || !memberId) {
      setMessage('Enter token, branch ID, and member ID to load the portal.')
      return
    }
    setMessage('Loading portal...')
    try {
      const [memberData, workoutData] = await Promise.all([
        apiFetch<Member>(apiBaseUrl, `/api/v1/members/${memberId}`, { token, query: { branch_id: branchId } }),
        listWorkouts(apiBaseUrl, token, branchId, memberId),
      ])
      setMember(memberData)
      setWorkouts(workoutData)
      setMessage('Portal data loaded.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not load portal data.')
    }
  }

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => undefined)
    }
  }, [])

  return (
    <main className="content-area" style={{ maxWidth: 1040, margin: '0 auto', padding: 24 }}>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Member self-service</div>
          <div className="page-title">FlowOS Member Portal</div>
          <div className="page-sub">PWA shell for profile, QR code, workouts, and subscription visibility.</div>
        </div>
        <button className="btn btn-primary" type="button" onClick={loadPortal}>Load portal</button>
      </div>

      <div className="card">
        <div className="table-toolbar">
          <input className="search-input" value={apiBaseUrl} onChange={(event) => setApiBaseUrl(event.target.value)} aria-label="API base URL" />
          <input className="search-input" value={branchId} onChange={(event) => setBranchId(event.target.value)} placeholder="Branch ID" />
          <input className="search-input" value={memberId} onChange={(event) => setMemberId(event.target.value)} placeholder="Member ID" />
          <input className="search-input" value={token} onChange={(event) => setToken(event.target.value)} placeholder="Access token" />
        </div>
        {message && <div className="empty-row">{message}</div>}
      </div>

      <div className="summary-row">
        <div className="summary-card">
          <div className="summary-label">Member</div>
          <div className="summary-amount" style={{ fontSize: 28 }}>{member?.full_name || 'Not loaded'}</div>
          <div className="summary-note">{member?.status || 'Status appears here after loading.'}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">QR Code</div>
          <div className="summary-amount" style={{ fontSize: 28 }}>{member?.member_code || '-'}</div>
          <div className="summary-note">Use this code at the front desk QR scanner.</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Workout logs</div>
          <div className="summary-amount">{workouts.length}</div>
          <div className="summary-note">Recent tracked workout entries.</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Workout history</div>
            <div className="card-subtitle">Progress entries logged by trainers or staff.</div>
          </div>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Exercise</th>
                <th>Volume</th>
              </tr>
            </thead>
            <tbody>
              {workouts.length > 0 ? workouts.map((workout) => (
                <tr key={workout.id}>
                  <td>{formatDate(workout.workout_date)}</td>
                  <td>{workout.exercise_name}</td>
                  <td>{[workout.sets && `${workout.sets} sets`, workout.reps && `${workout.reps} reps`, workout.weight_kg && `${workout.weight_kg}kg`].filter(Boolean).join(' · ') || '-'}</td>
                </tr>
              )) : (
                <tr><td className="empty-row" colSpan={3}>No workouts loaded.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  )
}
