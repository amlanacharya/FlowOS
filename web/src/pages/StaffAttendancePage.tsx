import { type FormEvent, useCallback, useEffect, useState } from 'react'
import {
  compareStaffShifts,
  createStaffShift,
  listStaffAttendance,
  listStaffShifts,
  staffCheckin,
  staffCheckout,
} from '../api'
import type { ShiftComparison, StaffAttendance, StaffShift, StaffShiftCreate } from '../types'
import { errorMessage, formatDate } from '../utils'
import { SkeletonTableRows } from '../components/Skeleton'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  currentStaffId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const today = new Date().toISOString().slice(0, 10)

function toLocalDateTimeValue(date: string, time: string) {
  return `${date}T${time}:00`
}

function formatTime(value: string | null) {
  if (!value) return '-'
  return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function durationHours(record: StaffAttendance) {
  if (!record.checked_out_at) return 'In progress'
  const diff = new Date(record.checked_out_at).getTime() - new Date(record.checked_in_at).getTime()
  return `${Math.max(diff / 36e5, 0).toFixed(1)}h`
}

function formatHourDelta(comparison: ShiftComparison | null) {
  return typeof comparison?.difference === 'number' ? `${comparison.difference.toFixed(1)}h` : '-'
}

export default function StaffAttendancePage({
  apiBaseUrl,
  accessToken,
  branchId,
  currentStaffId,
  pushNotice,
}: Props) {
  const [records, setRecords] = useState<StaffAttendance[]>([])
  const [shifts, setShifts] = useState<StaffShift[]>([])
  const [comparison, setComparison] = useState<ShiftComparison | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [filterStaffId, setFilterStaffId] = useState('')
  const [dateFrom, setDateFrom] = useState(today)
  const [dateTo, setDateTo] = useState(today)
  const [shiftForm, setShiftForm] = useState({ staff_id: currentStaffId, date: today, start: '09:00', end: '18:00', notes: '' })

  const effectiveStaffId = filterStaffId.trim() || currentStaffId

  const refresh = useCallback(async () => {
    if (!branchId) return
    setLoading(true)
    try {
      const params = { staff_id: filterStaffId.trim() || undefined, date_from: dateFrom, date_to: dateTo }
      const [attendanceData, shiftData] = await Promise.all([
        listStaffAttendance(apiBaseUrl, accessToken, branchId, params),
        listStaffShifts(apiBaseUrl, accessToken, branchId, params),
      ])
      setRecords(attendanceData.items)
      setShifts(shiftData.items)

      if (effectiveStaffId) {
        const comparisonData = await compareStaffShifts(apiBaseUrl, accessToken, branchId, effectiveStaffId, {
          date_from: dateFrom,
          date_to: dateTo,
        })
        setComparison(comparisonData)
      } else {
        setComparison(null)
      }
    } catch (error) {
      pushNotice('error', 'Failed to load staff attendance', errorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [accessToken, apiBaseUrl, branchId, dateFrom, dateTo, effectiveStaffId, filterStaffId, pushNotice])

  useEffect(() => {
    void refresh()
  }, [refresh])

  async function handleCheckin() {
    setActionLoading(true)
    try {
      await staffCheckin(apiBaseUrl, accessToken, branchId)
      pushNotice('success', 'Checked in', 'Your staff attendance check-in was recorded.')
      await refresh()
    } catch (error) {
      pushNotice('error', 'Check-in failed', errorMessage(error))
    } finally {
      setActionLoading(false)
    }
  }

  async function handleCheckout() {
    setActionLoading(true)
    try {
      await staffCheckout(apiBaseUrl, accessToken)
      pushNotice('success', 'Checked out', 'Your staff attendance check-out was recorded.')
      await refresh()
    } catch (error) {
      pushNotice('error', 'Check-out failed', errorMessage(error))
    } finally {
      setActionLoading(false)
    }
  }

  async function handleCreateShift(event: FormEvent) {
    event.preventDefault()
    const staffId = shiftForm.staff_id.trim()
    if (!staffId) {
      pushNotice('error', 'Staff ID required', 'Enter a staff ID before assigning a shift.')
      return
    }

    const payload: StaffShiftCreate = {
      shift_date: toLocalDateTimeValue(shiftForm.date, '00:00'),
      shift_start: toLocalDateTimeValue(shiftForm.date, shiftForm.start),
      shift_end: toLocalDateTimeValue(shiftForm.date, shiftForm.end),
      shift_type: 'regular',
      notes: shiftForm.notes,
    }

    setActionLoading(true)
    try {
      await createStaffShift(apiBaseUrl, accessToken, branchId, staffId, payload)
      pushNotice('success', 'Shift assigned', 'The staff shift was created.')
      await refresh()
    } catch (error) {
      pushNotice('error', 'Shift assignment failed', errorMessage(error))
    } finally {
      setActionLoading(false)
    }
  }

  const todayRecords = records.filter((record) => record.attendance_date === today)
  const presentToday = new Set(todayRecords.map((record) => record.staff_id)).size
  const checkedInNow = records.filter((record) => !record.checked_out_at).length

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Staff operations</div>
          <div className="page-title">Staff Attendance</div>
          <div className="page-sub">Track check-ins, check-outs, assigned shifts, and scheduled-vs-actual coverage.</div>
        </div>
        <div className="page-actions">
          <button className="btn btn-secondary" type="button" onClick={handleCheckin} disabled={actionLoading}>
            Check in
          </button>
          <button className="btn btn-primary" type="button" onClick={handleCheckout} disabled={actionLoading}>
            Check out
          </button>
        </div>
      </div>

      <div className="page-body">
        <div className="summary-row">
          <div className="summary-card animate-in delay-1">
            <div className="summary-label">Present today</div>
            <div className="summary-amount">{presentToday}</div>
            <div className="summary-note">Unique staff with a recorded check-in today.</div>
          </div>
          <div className="summary-card animate-in delay-2">
            <div className="summary-label">Checked in now</div>
            <div className="summary-amount">{checkedInNow}</div>
            <div className="summary-note">Attendance records without a check-out time.</div>
          </div>
          <div className="summary-card animate-in delay-3">
            <div className="summary-label">Scheduled delta</div>
            <div className="summary-amount">{formatHourDelta(comparison)}</div>
            <div className="summary-note">Scheduled hours minus actual checked-out hours for the selected staff.</div>
          </div>
        </div>

        <div className="card animate-in delay-2">
          <div className="table-toolbar">
            <input className="search-input" value={filterStaffId} onChange={(event) => setFilterStaffId(event.target.value)} placeholder="Filter staff UUID" />
            <input className="toolbar-select" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <input className="toolbar-select" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
            <span className="table-count">{records.length} records</span>
          </div>

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Staff</th>
                  <th>Date</th>
                  <th>Check-in</th>
                  <th>Check-out</th>
                  <th>Duration</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <SkeletonTableRows count={5} />
                ) : records.length > 0 ? (
                  records.map((record) => (
                    <tr key={record.id}>
                      <td className="mono">{record.staff_id.slice(0, 8)}</td>
                      <td>{formatDate(record.attendance_date)}</td>
                      <td>{formatTime(record.checked_in_at)}</td>
                      <td>{formatTime(record.checked_out_at)}</td>
                      <td>{durationHours(record)}</td>
                      <td>{record.notes || '-'}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="empty-row">No staff attendance records match this filter.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card animate-in delay-3">
          <div className="card-header">
            <div>
              <div className="card-title">Shift assignment</div>
              <div className="card-subtitle">Create regular staff shifts and compare them against actual attendance.</div>
            </div>
          </div>

          <form className="table-toolbar" onSubmit={handleCreateShift}>
            <input className="search-input" value={shiftForm.staff_id} onChange={(event) => setShiftForm((current) => ({ ...current, staff_id: event.target.value }))} placeholder="Staff UUID" />
            <input className="toolbar-select" type="date" value={shiftForm.date} onChange={(event) => setShiftForm((current) => ({ ...current, date: event.target.value }))} />
            <input className="toolbar-select" type="time" value={shiftForm.start} onChange={(event) => setShiftForm((current) => ({ ...current, start: event.target.value }))} />
            <input className="toolbar-select" type="time" value={shiftForm.end} onChange={(event) => setShiftForm((current) => ({ ...current, end: event.target.value }))} />
            <button className="btn btn-primary" type="submit" disabled={actionLoading}>Assign shift</button>
          </form>

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Staff</th>
                  <th>Date</th>
                  <th>Start</th>
                  <th>End</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {shifts.length > 0 ? (
                  shifts.map((shift) => (
                    <tr key={shift.id}>
                      <td className="mono">{shift.staff_id.slice(0, 8)}</td>
                      <td>{formatDate(shift.shift_date)}</td>
                      <td>{formatTime(shift.shift_start)}</td>
                      <td>{formatTime(shift.shift_end)}</td>
                      <td>{shift.shift_type}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="empty-row">No shifts match this filter.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  )
}
