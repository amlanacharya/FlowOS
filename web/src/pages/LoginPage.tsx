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
  const [email, setEmail] = useState('owner@fitlife.com')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [showApi, setShowApi] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
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
    } catch (error) {
      pushNotice('error', 'Login failed', errorMessage(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-shell">
      <div className="login-orb login-orb-1" />
      <div className="login-orb login-orb-2" />

      <section className="login-stage">
        <div className="login-panel animate-in">
          <div>
            <div className="login-brand">
              <div className="login-logo-mark">FO</div>
              <div>
                <div className="login-brand-name">FlowOS</div>
                <div className="login-brand-sub">Gym management workspace</div>
              </div>
            </div>

            <h1 className="login-heading">Run the floor, not the spreadsheet.</h1>
            <p className="login-sub">
              Shift from scattered ledgers to one operating surface for leads, members, collections, and branch setup.
            </p>

            <div className="login-highlights">
              <div className="login-highlight">
                <div className="login-highlight-label">Daily pulse</div>
                <div className="login-highlight-value">Today&apos;s roster</div>
                <div className="login-highlight-copy">
                  Track intake, collections, and renewals from one place without switching tabs.
                </div>
              </div>
              <div className="login-highlight">
                <div className="login-highlight-label">Branch ready</div>
                <div className="login-highlight-value">One login</div>
                <div className="login-highlight-copy">
                  Staff sessions, branch override, and API health stay visible from the first screen.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="login-card animate-in delay-2">
        <div className="page-eyebrow">Staff access</div>
        <div className="page-title" style={{ fontSize: 'clamp(2.2rem, 4vw, 3.6rem)' }}>
          Sign in
        </div>
        <div className="page-sub">
          Use your staff credentials to open the operations console.
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="field">
            <label className="field-label" htmlFor="login-email">Email address</label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="owner@fitlife.com"
              required
              autoFocus
            />
          </div>

          <div className="field">
            <label className="field-label" htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          <button className="btn btn-primary login-submit" type="submit" disabled={busy}>
            {busy ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <button className="api-toggle-btn" type="button" onClick={() => setShowApi((value) => !value)}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points={showApi ? '18 15 12 9 6 15' : '6 9 12 15 18 9'} />
          </svg>
          {showApi ? 'Hide API settings' : 'Configure API URL'}
        </button>

        {showApi && (
          <div className="field animate-in" style={{ marginTop: 14 }}>
            <label className="field-label" htmlFor="login-api-url">API base URL</label>
            <input
              id="login-api-url"
              type="url"
              value={apiBaseUrl}
              onChange={(event) => onApiBaseUrlChange(event.target.value)}
              placeholder="http://127.0.0.1:8000"
            />
            <div className="field-hint">
              Point this to the FlowOS backend you want this workspace to use.
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
