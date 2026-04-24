import { useCallback, useEffect, useState } from 'react'
import './App.css'
import { apiFetch } from './api'
import type { UserProfile } from './types'
import { errorMessage } from './utils'
import Sidebar from './components/Sidebar'
import NoticeStack, { type Notice, type Tone } from './components/NoticeStack'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import LeadsPage from './pages/LeadsPage'
import MembersPage from './pages/MembersPage'
import PaymentsPage from './pages/PaymentsPage'
import SettingsPage from './pages/SettingsPage'

type Page = 'dashboard' | 'leads' | 'members' | 'payments' | 'settings'

function read(key: string, fallback = '') {
  if (typeof window === 'undefined') return fallback
  return window.localStorage.getItem(key) ?? fallback
}

export default function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState(() => read('flowos-api-base', 'http://localhost:8000'))
  const [accessToken, setAccessToken] = useState(() => read('flowos-access-token'))
  const [refreshToken, setRefreshToken] = useState(() => read('flowos-refresh-token'))
  const [branchOverride, setBranchOverride] = useState(() => read('flowos-branch-override'))
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [currentPage, setCurrentPage] = useState<Page>('dashboard')
  const [health, setHealth] = useState<'checking' | 'online' | 'offline'>('checking')
  const [notices, setNotices] = useState<Notice[]>([])

  const pushNotice = useCallback((tone: Tone, title: string, detail: string) => {
    setNotices((prev) => [
      { id: Date.now() + Math.random(), tone, title, detail },
      ...prev,
    ].slice(0, 4))
  }, [])

  const dismissNotice = useCallback((id: number) => {
    setNotices((prev) => prev.filter((n) => n.id !== id))
  }, [])

  const branchId = branchOverride.trim() || profile?.branch_id || ''

  // Persist settings
  useEffect(() => { window.localStorage.setItem('flowos-api-base', apiBaseUrl) }, [apiBaseUrl])
  useEffect(() => { window.localStorage.setItem('flowos-access-token', accessToken) }, [accessToken])
  useEffect(() => { window.localStorage.setItem('flowos-refresh-token', refreshToken) }, [refreshToken])
  useEffect(() => { window.localStorage.setItem('flowos-branch-override', branchOverride) }, [branchOverride])

  // Health check
  useEffect(() => {
    setHealth('checking')
    apiFetch<{ status: string }>(apiBaseUrl, '/health')
      .then(() => setHealth('online'))
      .catch(() => setHealth('offline'))
  }, [apiBaseUrl])

  // Restore profile on mount
  useEffect(() => {
    if (!accessToken) { setProfile(null); return }
    apiFetch<UserProfile>(apiBaseUrl, '/api/v1/auth/me', { token: accessToken })
      .then(setProfile)
      .catch((err) => {
        pushNotice('error', 'Session expired', errorMessage(err))
        setProfile(null)
        setAccessToken('')
        setRefreshToken('')
      })
  }, [accessToken, apiBaseUrl])

  function handleLogin(at: string, rt: string, p: UserProfile) {
    setAccessToken(at)
    setRefreshToken(rt)
    setProfile(p)
    pushNotice('success', 'Signed in', `Welcome back, ${p.full_name}.`)
    setCurrentPage('dashboard')
  }

  function handleLogout() {
    setAccessToken('')
    setRefreshToken('')
    setProfile(null)
    setBranchOverride('')
    pushNotice('info', 'Signed out', 'Session cleared.')
  }

  function handleApiBaseUrlChange(url: string) {
    setApiBaseUrl(url)
  }

  // Show login if no token
  if (!accessToken) {
    return (
      <>
        <LoginPage
          apiBaseUrl={apiBaseUrl}
          onApiBaseUrlChange={handleApiBaseUrlChange}
          onLogin={handleLogin}
          pushNotice={pushNotice}
        />
        <NoticeStack notices={notices} onDismiss={dismissNotice} />
      </>
    )
  }

  const pageProps = { apiBaseUrl, accessToken, branchId, pushNotice }

  return (
    <>
      <div className="app-shell">
        <Sidebar
          currentPage={currentPage}
          onNavigate={setCurrentPage}
          onLogout={handleLogout}
          userName={profile?.full_name ?? ''}
          userRole={profile?.role ?? ''}
          health={health}
        />
        <div className="content-area">
          {currentPage === 'dashboard' && <DashboardPage {...pageProps} />}
          {currentPage === 'leads'     && <LeadsPage     {...pageProps} />}
          {currentPage === 'members'   && <MembersPage   {...pageProps} />}
          {currentPage === 'payments'  && <PaymentsPage  {...pageProps} />}
          {currentPage === 'settings'  && (
            <SettingsPage
              apiBaseUrl={apiBaseUrl}
              onApiBaseUrlChange={handleApiBaseUrlChange}
              accessToken={accessToken}
              profile={profile}
              branchOverride={branchOverride}
              onBranchOverrideChange={setBranchOverride}
              pushNotice={pushNotice}
            />
          )}
        </div>
      </div>
      <NoticeStack notices={notices} onDismiss={dismissNotice} />
    </>
  )
}
