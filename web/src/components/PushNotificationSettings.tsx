import { useCallback, useEffect, useState } from 'react'
import type { Notice } from './NoticeStack'

type Props = {
  apiBaseUrl: string
  accessToken: string
  memberId: string
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void
}

export function PushNotificationSettings({
  apiBaseUrl,
  accessToken,
  memberId,
  pushNotice,
}: Props) {
  const [optedIn, setOptedIn] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isSupported] = useState(() => 'serviceWorker' in navigator && 'PushManager' in window)

  const checkStatus = useCallback(async () => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/members/${memberId}/push-status`,
        { headers: { Authorization: `Bearer ${accessToken}` } },
      )
      const data = await response.json()
      setOptedIn(data.opted_in)
    } catch (err) {
      console.error('Failed to check push status:', err)
    }
  }, [accessToken, apiBaseUrl, memberId])

  useEffect(() => {
    void checkStatus()
  }, [checkStatus])

  async function handleSubscribe() {
    if (!isSupported) {
      pushNotice('error', 'Not supported', 'Web push not supported on this device')
      return
    }

    setIsLoading(true)
    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: import.meta.env.VITE_VAPID_PUBLIC_KEY,
      })

      const response = await fetch(
        `${apiBaseUrl}/api/v1/members/${memberId}/push-subscribe`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            token: JSON.stringify(subscription.toJSON()),
          }),
        },
      )

      if (response.ok) {
        setOptedIn(true)
        pushNotice('success', 'Subscribed', 'Push notifications enabled')
      } else {
        pushNotice('error', 'Subscription failed', 'Could not save subscription')
      }
    } catch (err) {
      pushNotice('error', 'Subscription error', String(err))
    } finally {
      setIsLoading(false)
    }
  }

  async function handleUnsubscribe() {
    setIsLoading(true)
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/members/${memberId}/push-unsubscribe`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${accessToken}` },
        },
      )

      if (response.ok) {
        setOptedIn(false)
        pushNotice('success', 'Unsubscribed', 'Push notifications disabled')
      }
    } catch (err) {
      pushNotice('error', 'Error', String(err))
    } finally {
      setIsLoading(false)
    }
  }

  if (!isSupported) {
    return (
      <div style={{ padding: '1rem', background: '#f5f5f5', borderRadius: '6px' }}>
        <p style={{ margin: 0, color: '#666', fontSize: '0.875rem' }}>
          Web push notifications not supported on this browser
        </p>
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem', background: '#f5f5f5', borderRadius: '6px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>Push Notifications</div>
          <div style={{ fontSize: '0.875rem', color: '#666' }}>
            {optedIn ? 'Enabled' : 'Disabled'}
          </div>
        </div>
        <button
          onClick={optedIn ? handleUnsubscribe : handleSubscribe}
          disabled={isLoading}
          style={{
            padding: '0.5rem 1rem',
            background: optedIn ? '#ef5350' : '#4caf50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontSize: '0.875rem',
          }}
        >
          {isLoading ? 'Processing...' : optedIn ? 'Disable' : 'Enable'}
        </button>
      </div>
    </div>
  )
}
