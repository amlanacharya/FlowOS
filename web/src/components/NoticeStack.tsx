import { useEffect } from 'react'

export type Tone = 'success' | 'error' | 'info' | 'warning'

export type Notice = {
  id: number
  tone: Tone
  title: string
  detail: string
}

type Props = {
  notices: Notice[]
  onDismiss: (id: number) => void
}

export default function NoticeStack({ notices, onDismiss }: Props) {
  useEffect(() => {
    if (notices.length === 0) return
    const latest = notices[notices.length - 1]
    const timer = setTimeout(() => onDismiss(latest.id), 4000)
    return () => clearTimeout(timer)
  }, [notices, onDismiss])

  if (notices.length === 0) return null

  return (
    <div className="notice-stack">
      {notices.map((n) => (
        <div
          key={n.id}
          className={`notice notice-${n.tone}`}
          onClick={() => onDismiss(n.id)}
          style={{ cursor: 'pointer' }}
        >
          <div className="notice-dot" />
          <div className="notice-content">
            <div className="notice-title">{n.title}</div>
            <div className="notice-detail">{n.detail}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
