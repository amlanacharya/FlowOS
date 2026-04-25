import { type FormEvent, useState } from 'react'
import { createAutomationRule, listAutomationRules, updateAutomationRule } from '../api'
import type { AutomationRule, AutomationRuleCreate } from '../types'
import { errorMessage, formatDate } from '../utils'
import type { Notice } from '../components/NoticeStack'
import { useAsyncData } from '../hooks/useAsyncData'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const defaultRule: AutomationRuleCreate = {
  name: 'Remind members before expiry',
  trigger_event: 'subscription_expiring',
  threshold_days: 7,
  threshold_amount: null,
  action: 'send_whatsapp',
}

export default function AutomationPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [rules, setRules] = useState<AutomationRule[]>([])
  const [form, setForm] = useState<AutomationRuleCreate>(defaultRule)
  const [submitting, setSubmitting] = useState(false)

  const { loading, refresh } = useAsyncData(
    () => listAutomationRules(apiBaseUrl, accessToken, branchId),
    [accessToken, apiBaseUrl, branchId, pushNotice],
    (data) => setRules(data.items),
    pushNotice,
    'Failed to load automation rules',
  )

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    try {
      await createAutomationRule(apiBaseUrl, accessToken, branchId, form)
      setForm(defaultRule)
      pushNotice('success', 'Rule created', 'Automation rule is ready to evaluate when the worker is enabled.')
      await refresh()
    } catch (error) {
      pushNotice('error', 'Rule creation failed', errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  async function toggle(rule: AutomationRule) {
    try {
      await updateAutomationRule(apiBaseUrl, accessToken, branchId, rule.id, { is_active: !rule.is_active })
      await refresh()
    } catch (error) {
      pushNotice('error', 'Rule update failed', errorMessage(error))
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Automation workspace</div>
          <div className="page-title">Rules</div>
          <div className="page-sub">Create templates for renewal reminders, stale leads, and overdue dues.</div>
        </div>
        <div className="page-actions">
          <span className="badge badge-active">{loading ? 'Loading' : `${rules.length} rules`}</span>
        </div>
      </div>

      <div className="page-body">
        <div className="split-grid">
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Create rule</div>
                <div className="card-subtitle">Worker execution is a P4 concern; this stores rule definitions now.</div>
              </div>
            </div>
            <form className="drawer-body" onSubmit={handleSubmit}>
              <div className="field">
                <label className="field-label" htmlFor="rule-name">Name</label>
                <input id="rule-name" value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} required />
              </div>
              <div className="field">
                <label className="field-label" htmlFor="trigger">Trigger</label>
                <select id="trigger" value={form.trigger_event} onChange={(event) => setForm((current) => ({ ...current, trigger_event: event.target.value as AutomationRuleCreate['trigger_event'] }))}>
                  <option value="subscription_expiring">Subscription expiring</option>
                  <option value="lead_stale">Lead stale</option>
                  <option value="dues_overdue">Dues overdue</option>
                </select>
              </div>
              <div className="summary-row">
                <input className="toolbar-select" type="number" min="1" value={form.threshold_days} onChange={(event) => setForm((current) => ({ ...current, threshold_days: Number(event.target.value) }))} />
                <select className="toolbar-select" value={form.action} onChange={(event) => setForm((current) => ({ ...current, action: event.target.value as AutomationRuleCreate['action'] }))}>
                  <option value="send_whatsapp">Send WhatsApp</option>
                  <option value="alert_manager">Alert manager</option>
                </select>
              </div>
              <button className="btn btn-primary" type="submit" disabled={submitting}>{submitting ? 'Creating...' : 'Create rule'}</button>
            </form>
          </div>

          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Active rules</div>
                <div className="card-subtitle">Toggle rules without deleting their configuration.</div>
              </div>
            </div>
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th>Name</th><th>Trigger</th><th>Threshold</th><th>Created</th><th>Status</th></tr></thead>
                <tbody>
                  {rules.length > 0 ? rules.map((rule) => (
                    <tr key={rule.id}>
                      <td>{rule.name}</td>
                      <td>{rule.trigger_event.replaceAll('_', ' ')}</td>
                      <td>{rule.threshold_days} days</td>
                      <td>{formatDate(rule.created_at)}</td>
                      <td><button className="btn btn-secondary" type="button" onClick={() => toggle(rule)}>{rule.is_active ? 'Active' : 'Paused'}</button></td>
                    </tr>
                  )) : <tr><td className="empty-row" colSpan={5}>No automation rules yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
