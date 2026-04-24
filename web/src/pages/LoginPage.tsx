import { type FormEvent, useState } from 'react'
import { apiFetch } from '../api'
import type { TokenResponse, UserProfile } from '../types'
import { errorMessage } from '../utils'
import type { Notice } from '../components/NoticeStack'

type Props = {
  apiBaseUrl: string
  onApiBaseUrlChange: (url: string) => void
  onLogin: (accessToken: string, refreshToken: string, profile: UserProfile) => void
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

export default function LoginPage({ apiBaseUrl, onApiBaseUrlChange, onLogin, pushNotice }: Props) {
  const [email, setEmail] = useState('owner@gym.com')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [showApi, setShowApi] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      const tokens = await apiFetch<TokenResponse>(apiBaseUrl, '/api/v1/auth/login', {
        method: 'POST',
        body: { email, password },
      })
      const profile = await apiFetch<UserProfile>(apiBaseUrl, '/api/v1/auth/me', {
        token: tokens.access_token,
      })
      onLogin(tokens.access_token, tokens.refresh_token, profile)
    } catch (err) {
      pushNotice('error', 'Login failed', errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-shell">
      <div className="login-orb login-orb-1" />
      <div className="login-orb login-orb-2" />

      <div className="login-card">
        <div className="login-brand">
          <div className="login-logo-mark">F</div>
          <div>
            <div className="login-brand-name">FLOWOS</div>
            <div className="login-brand-sub">Gym Management</div>
          </div>
        </div>

        <div className="login-heading">Welcome back</div>
        <div className="login-sub">Sign in with your staff credentials to continue.</div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="field">
            <label className="field-label">Email address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="staff@gym.com"
              required
              autoFocus
            />
          </div>
          <div className="field">
            <label className="field-label">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          <button className="btn btn-primary login-submit" type="submit" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div style={{ marginTop: 20 }}>
          <button className="api-toggle-btn" type="button" onClick={() => setShowApi((v) => !v)}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points={showApi ? '18 15 12 9 6 15' : '6 9 12 15 18 9'} />
            </svg>
            {showApi ? 'Hide API settings' : 'Configure API URL'}
          </button>

          {showApi && (
            <div className="field">
              <label className="field-label">API base URL</label>
              <input
                type="url"
                value={apiBaseUrl}
                onChange={(e) => onApiBaseUrlChange(e.target.value)}
                placeholder="http://localhost:8000"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
