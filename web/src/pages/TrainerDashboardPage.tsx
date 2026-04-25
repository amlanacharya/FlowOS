import { useMemo, useState } from 'react'
import { markTrainerAttendance, trainerToday } from '../api'
import type { TrainerSession } from '../types'
import { errorMessage, formatDate } from '../utils'
import Skeleton from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'
import { useAsyncData } from '../hooks/useAsyncData'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

function sessionTime(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function TrainerDashboardPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [sessions, setSessions] = useState<TrainerSession[]>([])
  const [updating, setUpdating] = useState('')

  const { loading, refresh } = useAsyncData(
    () => trainerToday(apiBaseUrl, accessToken, branchId),
    [accessToken, apiBaseUrl, branchId, pushNotice],
    setSessions,
    pushNotice,
    'Failed to load trainer schedule',
  )

  async function mark(enrollmentId: string, attended: boolean) {
    setUpdating(enrollmentId)
    try {
      await markTrainerAttendance(apiBaseUrl, accessToken, branchId, enrollmentId, attended)
      pushNotice('success', attended ? 'Marked attended' : 'Marked absent', 'Class attendance updated.')
      await refresh()
    } catch (error) {
      pushNotice('error', 'Attendance update failed', errorMessage(error))
    } finally {
      setUpdating('')
    }
  }

  const totalMembers = useMemo(
    () => sessions.reduce((sum, session) => sum + session.members.length, 0),
    [sessions],
  )

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Trainer floor view</div>
          <div className="page-title">Today&apos;s Sessions</div>
          <div className="page-sub">Mobile-friendly session roster with member attendance actions and no financial data.</div>
        </div>
        <div className="page-actions">
          <span className="badge badge-active">{sessions.length} sessions</span>
          <span className="badge badge-new">{totalMembers} enrolled</span>
        </div>
      </div>

      <div className="page-body">
        {loading ? (
          <div className="summary-row">
            <Skeleton variant="kpi" />
            <Skeleton variant="kpi" />
            <Skeleton variant="kpi" />
          </div>
        ) : sessions.length > 0 ? (
          <div className="split-grid">
            {sessions.map((session) => (
              <div className="card animate-in" key={session.session_id}>
                <div className="card-header">
                  <div>
                    <div className="card-title">{sessionTime(session.scheduled_at)} session</div>
                    <div className="card-subtitle">
                      {formatDate(session.scheduled_at)} · {session.duration_minutes} min · {session.enrolled_count}/{session.capacity}
                    </div>
                  </div>
                </div>
                <div className="card-body">
                  {session.members.length > 0 ? (
                    <div className="dues-list">
                      {session.members.map((member) => (
                        <div className="dues-row" key={member.enrollment_id}>
                          <div>
                            <div className="dues-name">{member.member_name}</div>
                            <div className="dues-meta">{member.attended ? 'Attended' : member.cancelled ? 'Cancelled' : 'Not marked'}</div>
                          </div>
                          <div style={{ display: 'flex', gap: 8 }}>
                            <button className="btn btn-secondary" type="button" disabled={updating === member.enrollment_id} onClick={() => mark(member.enrollment_id, false)}>
                              Absent
                            </button>
                            <button className="btn btn-primary" type="button" disabled={updating === member.enrollment_id} onClick={() => mark(member.enrollment_id, true)}>
                              Attended
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-row">No members enrolled in this session yet.</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card">
            <div className="empty-row">No sessions assigned today.</div>
          </div>
        )}
      </div>
    </>
  )
}
