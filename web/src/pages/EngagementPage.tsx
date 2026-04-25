import { type FormEvent, useMemo, useState } from 'react'
import { createWorkout, feedbackSummary, listFeedback, listWorkouts } from '../api'
import type { FeedbackSummary, MemberFeedback, WorkoutLog, WorkoutLogCreate } from '../types'
import { errorMessage, formatDate } from '../utils'
import { SkeletonTableRows } from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'
import { useAsyncData } from '../hooks/useAsyncData'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const defaultWorkout = {
  member_id: '',
  exercise_name: '',
  sets: '',
  reps: '',
  weight_kg: '',
  notes: '',
}

export default function EngagementPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [memberId, setMemberId] = useState('')
  const [workouts, setWorkouts] = useState<WorkoutLog[]>([])
  const [feedback, setFeedback] = useState<MemberFeedback[]>([])
  const [summary, setSummary] = useState<FeedbackSummary | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState(defaultWorkout)

  const { loading } = useAsyncData(
    async () => Promise.all([
      feedbackSummary(apiBaseUrl, accessToken, branchId),
      listFeedback(apiBaseUrl, accessToken, branchId),
    ]),
    [accessToken, apiBaseUrl, branchId, pushNotice],
    ([summaryData, feedbackData]) => {
      setSummary(summaryData)
      setFeedback(feedbackData.items)
    },
    pushNotice,
    'Failed to load engagement data',
  )

  async function loadWorkouts(targetMemberId = memberId.trim()) {
    if (!targetMemberId) return
    try {
      setWorkouts(await listWorkouts(apiBaseUrl, accessToken, branchId, targetMemberId))
    } catch (error) {
      pushNotice('error', 'Failed to load workouts', errorMessage(error))
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const payload: WorkoutLogCreate = {
      member_id: form.member_id,
      exercise_name: form.exercise_name,
      sets: form.sets ? Number(form.sets) : undefined,
      reps: form.reps ? Number(form.reps) : undefined,
      weight_kg: form.weight_kg ? Number(form.weight_kg) : undefined,
      notes: form.notes || undefined,
    }

    setSubmitting(true)
    try {
      await createWorkout(apiBaseUrl, accessToken, branchId, payload)
      setMemberId(form.member_id)
      setForm(defaultWorkout)
      pushNotice('success', 'Workout logged', 'The workout entry was added.')
      await loadWorkouts(payload.member_id)
    } catch (error) {
      pushNotice('error', 'Workout log failed', errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  const averageRating = typeof summary?.average_rating === 'number' ? summary.average_rating.toFixed(1) : '0.0'
  const workoutRows = useMemo(() => workouts, [workouts])

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Member engagement</div>
          <div className="page-title">Workouts & Feedback</div>
          <div className="page-sub">Capture workout progress and monitor member feedback from one operational view.</div>
        </div>
        <div className="page-actions">
          <span className="badge badge-active">{averageRating} avg rating</span>
          <span className="badge badge-new">{summary?.total ?? 0} recent feedback</span>
        </div>
      </div>

      <div className="page-body">
        <div className="split-grid">
          <div className="card animate-in delay-1">
            <div className="card-header">
              <div>
                <div className="card-title">Log workout</div>
                <div className="card-subtitle">Trainer or manager can log on behalf of a member.</div>
              </div>
            </div>
            <form className="drawer-body" onSubmit={handleSubmit}>
              <div className="field">
                <label className="field-label" htmlFor="workout-member">Member UUID</label>
                <input id="workout-member" value={form.member_id} onChange={(event) => setForm((current) => ({ ...current, member_id: event.target.value }))} required />
              </div>
              <div className="field">
                <label className="field-label" htmlFor="exercise">Exercise</label>
                <input id="exercise" value={form.exercise_name} onChange={(event) => setForm((current) => ({ ...current, exercise_name: event.target.value }))} placeholder="Deadlift" required />
              </div>
              <div className="summary-row">
                <input className="toolbar-select" type="number" min="0" placeholder="Sets" value={form.sets} onChange={(event) => setForm((current) => ({ ...current, sets: event.target.value }))} />
                <input className="toolbar-select" type="number" min="0" placeholder="Reps" value={form.reps} onChange={(event) => setForm((current) => ({ ...current, reps: event.target.value }))} />
                <input className="toolbar-select" type="number" min="0" step="0.5" placeholder="Weight kg" value={form.weight_kg} onChange={(event) => setForm((current) => ({ ...current, weight_kg: event.target.value }))} />
              </div>
              <div className="field">
                <label className="field-label" htmlFor="workout-notes">Notes</label>
                <input id="workout-notes" value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} />
              </div>
              <button className="btn btn-primary" type="submit" disabled={submitting}>
                {submitting ? 'Logging...' : 'Log workout'}
              </button>
            </form>
          </div>

          <div className="card animate-in delay-2">
            <div className="card-header">
              <div>
                <div className="card-title">Workout history</div>
                <div className="card-subtitle">Load a member&apos;s recent workout log.</div>
              </div>
            </div>
            <div className="table-toolbar">
              <input className="search-input" value={memberId} onChange={(event) => setMemberId(event.target.value)} placeholder="Member UUID" />
              <button className="btn btn-secondary" type="button" onClick={() => loadWorkouts()}>Load</button>
            </div>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Exercise</th>
                    <th>Volume</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {workoutRows.length > 0 ? workoutRows.map((workout) => (
                    <tr key={workout.id}>
                      <td>{formatDate(workout.workout_date)}</td>
                      <td>{workout.exercise_name}</td>
                      <td>{[workout.sets && `${workout.sets} sets`, workout.reps && `${workout.reps} reps`, workout.weight_kg && `${workout.weight_kg}kg`].filter(Boolean).join(' · ') || '-'}</td>
                      <td>{workout.notes || '-'}</td>
                    </tr>
                  )) : (
                    <tr><td className="empty-row" colSpan={4}>No workout rows loaded.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="card animate-in delay-3">
          <div className="card-header">
            <div>
              <div className="card-title">Feedback monitor</div>
              <div className="card-subtitle">Last 30-day average and latest member comments.</div>
            </div>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rating</th>
                  <th>Comment</th>
                  <th>Submitted</th>
                </tr>
              </thead>
              <tbody>
                {loading ? <SkeletonTableRows count={3} /> : feedback.length > 0 ? feedback.map((item) => (
                  <tr key={item.id}>
                    <td>{item.rating}/5</td>
                    <td>{item.comment || '-'}</td>
                    <td>{formatDate(item.submitted_at)}</td>
                  </tr>
                )) : (
                  <tr><td className="empty-row" colSpan={3}>No feedback submitted yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  )
}
