import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  createSubscriptionAdjustment,
  listMembershipTracking,
  listPauseHistory,
  listPlans,
  listReminderChecklist,
  listSubscriptionAdjustments,
  pauseSubscription,
  renewSubscription,
  resumeSubscription,
} from '../api'
import type {
  MembershipTrackingItem,
  PauseHistoryItem,
  PlanOption,
  ReminderChecklistItem,
  SubscriptionAdjustmentItem,
} from '../types'
import { errorMessage, formatCurrency, formatDate } from '../utils'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

export default function MembershipTrackingPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [items, setItems] = useState<MembershipTrackingItem[]>([])
  const [plans, setPlans] = useState<PlanOption[]>([])
  const [checklist, setChecklist] = useState<ReminderChecklistItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSubId, setSelectedSubId] = useState<string>('')
  const [history, setHistory] = useState<PauseHistoryItem[]>([])
  const [adjustments, setAdjustments] = useState<SubscriptionAdjustmentItem[]>([])
  const [pauseDate, setPauseDate] = useState('')
  const [resumeDate, setResumeDate] = useState('')
  const [actionReason, setActionReason] = useState('')
  const [adjustmentDays, setAdjustmentDays] = useState('')
  const [adjustmentReason, setAdjustmentReason] = useState('')
  const [adjustmentSubmitting, setAdjustmentSubmitting] = useState(false)
  const [renewDrawerOpen, setRenewDrawerOpen] = useState(false)
  const [renewPlanId, setRenewPlanId] = useState('')
  const [renewSubmitting, setRenewSubmitting] = useState(false)

  const selectedItem = useMemo(
    () => items.find((item) => item.subscription_id === selectedSubId) ?? null,
    [items, selectedSubId],
  )

  const fetchTrackingAndReminders = useCallback(async () => {
    setLoading(true)
    const [trackResult, reminderResult] = await Promise.allSettled([
      listMembershipTracking(apiBaseUrl, accessToken, branchId),
      listReminderChecklist(apiBaseUrl, accessToken, branchId),
    ])

    if (trackResult.status === 'fulfilled') {
      setItems(trackResult.value)
    } else {
      pushNotice('error', 'Failed to load membership tracking', errorMessage(trackResult.reason))
    }

    if (reminderResult.status === 'fulfilled') {
      setChecklist(reminderResult.value)
    } else {
      pushNotice('error', 'Failed to load reminder checklist', errorMessage(reminderResult.reason))
    }

    setLoading(false)
  }, [accessToken, apiBaseUrl, branchId, pushNotice])

  useEffect(() => {
    void fetchTrackingAndReminders()
  }, [fetchTrackingAndReminders])

  useEffect(() => {
    void listPlans(apiBaseUrl, accessToken, branchId)
      .then(setPlans)
      .catch((error) => pushNotice('error', 'Failed to load plans', errorMessage(error)))
  }, [accessToken, apiBaseUrl, branchId, pushNotice])

  useEffect(() => {
    if (!selectedSubId) {
      setHistory([])
      setAdjustments([])
      return
    }

    void Promise.allSettled([
      listPauseHistory(apiBaseUrl, accessToken, selectedSubId),
      listSubscriptionAdjustments(apiBaseUrl, accessToken, selectedSubId),
    ]).then(([historyResult, adjustmentResult]) => {
      if (historyResult.status === 'fulfilled') {
        setHistory(historyResult.value)
      } else {
        pushNotice('error', 'Failed to load pause history', errorMessage(historyResult.reason))
      }

      if (adjustmentResult.status === 'fulfilled') {
        setAdjustments(adjustmentResult.value)
      } else {
        pushNotice('error', 'Failed to load adjustment history', errorMessage(adjustmentResult.reason))
      }
    })
  }, [accessToken, apiBaseUrl, pushNotice, selectedSubId])

  async function handlePause() {
    if (!selectedSubId || !pauseDate) {
      pushNotice('info', 'Pause date required', 'Choose subscription and pause date first.')
      return
    }
    try {
      await pauseSubscription(apiBaseUrl, accessToken, selectedSubId, pauseDate, actionReason || undefined)
      pushNotice('success', 'Subscription paused', 'Pause entry recorded.')
      await fetchTrackingAndReminders()
      setHistory(await listPauseHistory(apiBaseUrl, accessToken, selectedSubId))
      setAdjustments(await listSubscriptionAdjustments(apiBaseUrl, accessToken, selectedSubId))
    } catch (error) {
      pushNotice('error', 'Pause failed', errorMessage(error))
    }
  }

  async function handleResume() {
    if (!selectedSubId || !resumeDate) {
      pushNotice('info', 'Resume date required', 'Choose subscription and resume date first.')
      return
    }
    try {
      await resumeSubscription(apiBaseUrl, accessToken, selectedSubId, resumeDate)
      pushNotice('success', 'Subscription resumed', 'Resume entry recorded.')
      await fetchTrackingAndReminders()
      setHistory(await listPauseHistory(apiBaseUrl, accessToken, selectedSubId))
      setAdjustments(await listSubscriptionAdjustments(apiBaseUrl, accessToken, selectedSubId))
    } catch (error) {
      pushNotice('error', 'Resume failed', errorMessage(error))
    }
  }

  function openRenewal() {
    if (!selectedItem) {
      pushNotice('info', 'Select a subscription', 'Choose a member row first, then renew.')
      return
    }
    setRenewPlanId(selectedItem.plan_id)
    setRenewDrawerOpen(true)
  }

  async function handleRenewal() {
    if (!selectedSubId || !renewPlanId) {
      pushNotice('info', 'Plan required', 'Pick a renewal plan before continuing.')
      return
    }

    setRenewSubmitting(true)
    try {
      await renewSubscription(apiBaseUrl, accessToken, selectedSubId, renewPlanId)
      pushNotice('success', 'Renewal completed', 'Renewal invoice generated for selected plan.')
      setRenewDrawerOpen(false)
      await fetchTrackingAndReminders()
      setHistory(await listPauseHistory(apiBaseUrl, accessToken, selectedSubId))
      setAdjustments(await listSubscriptionAdjustments(apiBaseUrl, accessToken, selectedSubId))
    } catch (error) {
      pushNotice('error', 'Renewal failed', errorMessage(error))
    } finally {
      setRenewSubmitting(false)
    }
  }

  async function handleAdjustment() {
    if (!selectedSubId) {
      pushNotice('info', 'Select a subscription', 'Choose a subscription row before adjusting days.')
      return
    }

    const parsedDays = Number.parseInt(adjustmentDays, 10)
    if (!Number.isInteger(parsedDays) || parsedDays === 0) {
      pushNotice('info', 'Invalid day count', 'Enter a positive or negative whole number of days.')
      return
    }

    setAdjustmentSubmitting(true)
    try {
      await createSubscriptionAdjustment(
        apiBaseUrl,
        accessToken,
        selectedSubId,
        parsedDays,
        adjustmentReason || undefined,
      )
      pushNotice('success', 'Adjustment saved', `Updated subscription by ${parsedDays} days.`)
      setAdjustmentDays('')
      setAdjustmentReason('')
      await fetchTrackingAndReminders()
      setAdjustments(await listSubscriptionAdjustments(apiBaseUrl, accessToken, selectedSubId))
    } catch (error) {
      pushNotice('error', 'Adjustment failed', errorMessage(error))
    } finally {
      setAdjustmentSubmitting(false)
    }
  }

  return (
    <>
      <div className="page-body">
        <div className="page-header">
          <div>
            <div className="page-eyebrow">Membership operations</div>
            <div className="page-title">Membership Tracking</div>
            <div className="page-sub">Manage renewals, pause/resume history, and pause-day impact by subscription.</div>
          </div>
          <div className="page-actions">
            <span className="badge badge-active">{checklist.length} reminders</span>
            <button type="button" className="btn btn-primary" onClick={openRenewal}>
              Renew selected
            </button>
          </div>
        </div>

        <div className="split-grid">
          <div className="card">
            <div className="card-header">
              <span className="card-title">Subscription list</span>
              <span className="card-meta">{items.length} records</span>
            </div>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Member</th>
                    <th>Status</th>
                    <th>End date</th>
                    <th>Pause days</th>
                    <th>Renewal</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={5} className="empty-row">Loading...</td>
                    </tr>
                  ) : items.length ? (
                    items.map((item) => (
                      <tr
                        key={item.subscription_id}
                        onClick={() => setSelectedSubId(item.subscription_id)}
                        style={{ cursor: 'pointer', background: selectedSubId === item.subscription_id ? 'rgba(13,148,136,0.08)' : undefined }}
                      >
                        <td>
                          <div className="table-name">{item.member_name}</div>
                          <div className="table-sub mono">{item.member_phone}</div>
                        </td>
                        <td>{item.status}</td>
                        <td>{formatDate(item.end_date)}</td>
                        <td>{item.total_pause_days}</td>
                        <td>{item.renewal_due_in_days} days</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="empty-row">No subscriptions found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Pause/Resume</span>
              <span className="card-meta">Date-driven controls</span>
            </div>
            <div className="card-body">
              <div className="field">
                <label className="field-label" htmlFor="pause-date">Pause date</label>
                <input id="pause-date" type="date" value={pauseDate} onChange={(event) => setPauseDate(event.target.value)} />
              </div>
              <div className="field" style={{ marginTop: 14 }}>
                <label className="field-label" htmlFor="resume-date">Resume date</label>
                <input id="resume-date" type="date" value={resumeDate} onChange={(event) => setResumeDate(event.target.value)} />
              </div>
              <div className="field" style={{ marginTop: 14 }}>
                <label className="field-label" htmlFor="pause-reason">Reason</label>
                <input id="pause-reason" value={actionReason} onChange={(event) => setActionReason(event.target.value)} />
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                <button type="button" className="btn btn-secondary" onClick={() => void handlePause()}>Pause</button>
                <button type="button" className="btn btn-primary" onClick={() => void handleResume()}>Resume</button>
              </div>
            </div>

            <div className="card-header">
              <span className="card-title">Pause history</span>
              <span className="card-meta">{history.length} events</span>
            </div>
            <div className="card-body">
              {history.length ? (
                history.map((row) => (
                  <div key={row.id} className="info-row">
                    <div>
                      <div className="table-name">
                        {formatDate(row.pause_date)} to {row.resume_date ? formatDate(row.resume_date) : 'Open'}
                      </div>
                      <div className="info-key">{row.reason || 'No reason provided'}</div>
                    </div>
                    <span className="info-val">{row.pause_days} days</span>
                  </div>
                ))
              ) : (
                <div className="empty-row">No pause history for selected subscription.</div>
              )}
            </div>

            <div className="card-header">
              <span className="card-title">Reminder checklist (T-3 to T+1)</span>
              <span className="card-meta">{checklist.length} due</span>
            </div>
            <div className="card-body">
              {checklist.length ? (
                checklist.map((row) => (
                  <div key={`${row.subscription_id}-${row.checkpoint_label}`} className="info-row">
                    <div>
                      <div className="table-name">{row.member_name}</div>
                      <div className="info-key">
                        {row.checkpoint_label} | End: {formatDate(row.end_date)} | {row.member_phone}
                      </div>
                    </div>
                    <span className="info-val">{formatCurrency(row.amount_due)}</span>
                  </div>
                ))
              ) : (
                <div className="empty-row">No reminder checkpoints in the current T-3 to T+1 window.</div>
              )}
            </div>

            <div className="card-header">
              <span className="card-title">Extra day adjustments</span>
              <span className="card-meta">{adjustments.length} entries</span>
            </div>
            <div className="card-body">
              <div className="field">
                <label className="field-label" htmlFor="adjust-days">Days (+ / -)</label>
                <input
                  id="adjust-days"
                  type="number"
                  value={adjustmentDays}
                  onChange={(event) => setAdjustmentDays(event.target.value)}
                  placeholder="Example: +3 or -2"
                />
              </div>
              <div className="field" style={{ marginTop: 12 }}>
                <label className="field-label" htmlFor="adjust-reason">Reason</label>
                <input
                  id="adjust-reason"
                  value={adjustmentReason}
                  onChange={(event) => setAdjustmentReason(event.target.value)}
                  placeholder="Medical pause adjustment, goodwill extension, manual correction"
                />
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => void handleAdjustment()}
                  disabled={adjustmentSubmitting}
                >
                  {adjustmentSubmitting ? 'Saving...' : 'Apply days'}
                </button>
              </div>
              <div style={{ marginTop: 16 }}>
                {adjustments.length ? (
                  adjustments.map((row) => (
                    <div key={row.id} className="info-row">
                      <div>
                        <div className="table-name">{row.days_delta > 0 ? `+${row.days_delta}` : row.days_delta} days</div>
                        <div className="info-key">{row.reason || 'No reason provided'}</div>
                      </div>
                      <span className="info-val">{formatDate(row.created_at)}</span>
                    </div>
                  ))
                ) : (
                  <div className="empty-row">No manual day adjustments recorded for this subscription.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className={`drawer-overlay ${renewDrawerOpen ? 'open' : ''}`} onClick={() => setRenewDrawerOpen(false)} />
      <div className={`drawer ${renewDrawerOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <span className="drawer-title">Renew membership</span>
          <button className="btn-icon" type="button" onClick={() => setRenewDrawerOpen(false)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="drawer-body">
          <div className="field">
            <label className="field-label">Selected member</label>
            <div className="field-hint">{selectedItem ? `${selectedItem.member_name} (${selectedItem.member_phone})` : 'No subscription selected'}</div>
          </div>

          <div className="field">
            <label className="field-label" htmlFor="renew-plan">Renewal plan</label>
            <select id="renew-plan" value={renewPlanId} onChange={(event) => setRenewPlanId(event.target.value)}>
              <option value="">Select plan</option>
              {plans.map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.name} ({plan.plan_type}) - {formatCurrency(plan.price)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="drawer-footer">
          <button className="btn btn-primary" type="button" disabled={renewSubmitting} style={{ flex: 1 }} onClick={() => void handleRenewal()}>
            {renewSubmitting ? 'Renewing...' : 'Confirm renewal'}
          </button>
          <button className="btn btn-ghost" type="button" onClick={() => setRenewDrawerOpen(false)}>
            Cancel
          </button>
        </div>
      </div>
    </>
  )
}
