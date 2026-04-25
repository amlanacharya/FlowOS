import { useState } from 'react'
import {
  getCampaignAnalytics,
  getDailySalesReport,
  getMonthlyRevenue,
  getPeakHours,
  getRetentionReport,
  getRevenueForecast,
} from '../api'
import type { CampaignAnalytics, DailySalesReport, MonthlyRevenue, PeakHourBucket, RetentionReport, RevenueForecast } from '../types'
import { formatCurrency } from '../utils'
import type { Notice } from '../components/NoticeStack'
import { useAsyncData } from '../hooks/useAsyncData'

type Props = {
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

const today = new Date().toISOString().slice(0, 10)

export default function ReportsPage({ apiBaseUrl, accessToken, branchId, pushNotice }: Props) {
  const [dailySales, setDailySales] = useState<DailySalesReport | null>(null)
  const [retention, setRetention] = useState<RetentionReport | null>(null)
  const [forecast, setForecast] = useState<RevenueForecast | null>(null)
  const [peakHours, setPeakHours] = useState<PeakHourBucket[]>([])
  const [monthlyRevenue, setMonthlyRevenue] = useState<MonthlyRevenue[]>([])
  const [campaigns, setCampaigns] = useState<CampaignAnalytics[]>([])

  const { loading } = useAsyncData(
    async () => Promise.all([
      getDailySalesReport(apiBaseUrl, accessToken, branchId, today),
      getRetentionReport(apiBaseUrl, accessToken, branchId),
      getRevenueForecast(apiBaseUrl, accessToken, branchId),
      getPeakHours(apiBaseUrl, accessToken, branchId),
      getMonthlyRevenue(apiBaseUrl, accessToken, branchId),
      getCampaignAnalytics(apiBaseUrl, accessToken, branchId),
    ]),
    [accessToken, apiBaseUrl, branchId, pushNotice],
    ([daily, retentionData, forecastData, peakData, monthlyData, campaignData]) => {
      setDailySales(daily)
      setRetention(retentionData)
      setForecast(forecastData)
      setPeakHours(peakData)
      setMonthlyRevenue(monthlyData)
      setCampaigns(campaignData)
    },
    pushNotice,
    'Failed to load reports',
  )

  const busiest = peakHours.reduce((best, bucket) => bucket.checkin_count > best.checkin_count ? bucket : best, { hour: 0, checkin_count: 0 })
  const revenueTotal = monthlyRevenue.reduce((sum, row) => sum + Number(row.total_revenue), 0)

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">Business intelligence</div>
          <div className="page-title">Reports</div>
          <div className="page-sub">Daily sales, retention, renewal forecast, peak usage, and marketing attribution.</div>
        </div>
        <div className="page-actions">
          <span className="badge badge-active">{loading ? 'Loading' : 'Live data'}</span>
        </div>
      </div>

      <div className="page-body">
        <div className="summary-row">
          <div className="summary-card">
            <div className="summary-label">Today&apos;s collection</div>
            <div className="summary-amount">{formatCurrency(Number(dailySales?.total_collection ?? 0))}</div>
            <div className="summary-note">{dailySales?.new_members ?? 0} new members, {dailySales?.leads_converted ?? 0} converted leads.</div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Churn risk</div>
            <div className="summary-amount">{retention?.churn_rate ?? 0}%</div>
            <div className="summary-note">{retention?.not_renewed_within_30d ?? 0} not renewed within 30 days.</div>
          </div>
          <div className="summary-card">
            <div className="summary-label">30-day forecast</div>
            <div className="summary-amount">{formatCurrency(Number(forecast?.next_30_days.projected_amount ?? 0))}</div>
            <div className="summary-note">{forecast?.next_30_days.count ?? 0} renewals due.</div>
          </div>
        </div>

        <div className="split-grid">
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Peak hour usage</div>
                <div className="card-subtitle">Busiest hour: {busiest.hour}:00 with {busiest.checkin_count} check-ins.</div>
              </div>
            </div>
            <div className="card-body">
              <div className="funnel-list">
                {peakHours.filter((bucket) => bucket.checkin_count > 0).slice(0, 8).map((bucket) => (
                  <div className="funnel-row" key={bucket.hour}>
                    <span className="funnel-label">{bucket.hour}:00</span>
                    <div className="funnel-bar-track">
                      <div className="funnel-bar-fill" style={{ width: `${Math.max(bucket.checkin_count * 8, 6)}%` }} />
                    </div>
                    <span className="funnel-count">{bucket.checkin_count}</span>
                  </div>
                ))}
                {peakHours.every((bucket) => bucket.checkin_count === 0) && <div className="empty-row">No check-ins in this period.</div>}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Monthly revenue</div>
                <div className="card-subtitle">{formatCurrency(revenueTotal)} over {monthlyRevenue.length || 0} months.</div>
              </div>
            </div>
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th>Month</th><th>Revenue</th><th>Payments</th></tr></thead>
                <tbody>
                  {monthlyRevenue.length > 0 ? monthlyRevenue.map((row) => (
                    <tr key={row.month}><td>{row.month}</td><td>{formatCurrency(Number(row.total_revenue))}</td><td>{row.payment_count}</td></tr>
                  )) : <tr><td className="empty-row" colSpan={3}>No monthly revenue yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Campaign attribution</div>
              <div className="card-subtitle">Lead conversion by UTM campaign.</div>
            </div>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>Campaign</th><th>Leads</th><th>Converted</th><th>Rate</th></tr></thead>
              <tbody>
                {campaigns.length > 0 ? campaigns.map((row) => (
                  <tr key={row.utm_campaign}><td>{row.utm_campaign}</td><td>{row.total_leads}</td><td>{row.converted}</td><td>{row.conversion_rate}%</td></tr>
                )) : <tr><td className="empty-row" colSpan={4}>No UTM campaigns captured yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  )
}
