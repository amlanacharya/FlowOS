import { useEffect, useRef, useState } from 'react'
import type { QrCheckinResponse } from '../types'

type PushNoticeFn = (tone: 'success' | 'error' | 'info' | 'warning', title: string, detail: string) => void

type Props = {
  open: boolean
  onClose: () => void
  onSuccess: (result: QrCheckinResponse) => void
  apiBaseUrl: string
  accessToken: string
  branchId: string
  pushNotice: PushNoticeFn
}

export function QrScannerModal({
  open,
  onClose,
  onSuccess,
  apiBaseUrl,
  accessToken,
  branchId,
  pushNotice,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState<QrCheckinResponse | null>(null)
  const [manualCode, setManualCode] = useState('')
  const [cameraError, setCameraError] = useState<string>('')

  // Start camera on modal open
  useEffect(() => {
    if (!open) return

    const startCamera = async () => {
      try {
        setCameraError('')
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
        })
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.play()
        }
      } catch (err) {
        setCameraError('Camera access denied or unavailable. Use manual entry instead.')
      }
    }

    startCamera()

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [open])

  const handleScan = async (memberCode: string) => {
    if (loading || success) return

    setLoading(true)
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/attendance/qr-checkin?branch_id=${branchId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ member_code: memberCode }),
        },
      )

      const data = await response.json()

      if (!response.ok) {
        pushNotice('error', 'Check-in failed', data.detail || '')
      } else {
        setSuccess(data)
        onSuccess(data)
        pushNotice('success', 'Check-in successful', `${data.member_name} has been checked in`)

        setTimeout(() => {
          setSuccess(null)
          setManualCode('')
        }, 3000)
      }
    } catch (err) {
      pushNotice('error', 'Network error', 'Failed to complete check-in')
    } finally {
      setLoading(false)
    }
  }

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (manualCode.trim()) {
      const code = manualCode.trim()
      setManualCode('')
      handleScan(code)
    }
  }

  if (!open) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>QR Code Check-in</h2>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {cameraError ? (
            <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
              {cameraError}
            </div>
          ) : (
            <div style={{ position: 'relative', marginBottom: '1rem' }}>
              <video
                ref={videoRef}
                style={{
                  width: '100%',
                  borderRadius: '8px',
                  display: success ? 'none' : 'block',
                  aspectRatio: '1',
                  objectFit: 'cover',
                  background: '#000',
                }}
              />

              {success && (
                <div className="card" style={{ padding: '1.5rem', textAlign: 'center', background: '#f5f5f5' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem', color: '#4caf50' }}>✓</div>
                  <h3 style={{ margin: '0 0 0.5rem 0' }}>{success.member_name}</h3>
                  {success.subscription_end_date && (
                    <p style={{ color: '#666', marginBottom: '0.5rem' }}>
                      Expires: {new Date(success.subscription_end_date).toLocaleDateString()}
                    </p>
                  )}
                  {success.amount_due > 0 && (
                    <p style={{ color: '#d32f2f', fontWeight: 'bold', margin: 0 }}>
                      Amount Due: ₹{success.amount_due.toFixed(2)}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          <form onSubmit={handleManualSubmit}>
            <label htmlFor="manual-code" style={{ display: 'block', marginBottom: '0.5rem' }}>
              <div style={{ fontSize: '0.875rem', marginBottom: '0.25rem', fontWeight: '500' }}>
                Enter member code:
              </div>
              <input
                id="manual-code"
                type="text"
                placeholder="Member code"
                value={manualCode}
                onChange={e => setManualCode(e.target.value)}
                disabled={loading || !!success}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  marginBottom: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '1rem',
                }}
              />
            </label>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !manualCode.trim() || !!success}
              style={{
                width: '100%',
                padding: '0.75rem',
                marginBottom: '0.5rem',
              }}
            >
              {loading ? 'Checking in...' : 'Check In'}
            </button>
          </form>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>

      <style>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          max-width: 500px;
          width: 90vw;
          max-height: 90vh;
          display: flex;
          flex-direction: column;
        }

        .modal-header {
          padding: 1.5rem;
          border-bottom: 1px solid #e0e0e0;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .modal-header h2 {
          margin: 0;
          font-size: 1.25rem;
        }

        .btn-close {
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: #666;
          padding: 0;
          width: 2rem;
          height: 2rem;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .btn-close:hover {
          color: #000;
        }

        .modal-body {
          padding: 1.5rem;
          flex: 1;
          overflow-y: auto;
        }

        .modal-footer {
          padding: 1rem 1.5rem;
          border-top: 1px solid #e0e0e0;
          display: flex;
          justify-content: flex-end;
          gap: 0.5rem;
        }

        .alert {
          padding: 1rem;
          border-radius: 6px;
        }

        .alert-error {
          background: #ffebee;
          color: #c62828;
          border: 1px solid #ef5350;
        }

        .card {
          border: 1px solid #e0e0e0;
          border-radius: 6px;
        }

        .btn {
          padding: 0.75rem 1.5rem;
          border-radius: 6px;
          border: none;
          cursor: pointer;
          font-size: 1rem;
          font-weight: 500;
        }

        .btn-primary {
          background: #6366f1;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background: #4f46e5;
        }

        .btn-primary:disabled {
          background: #d1d5db;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: #e5e7eb;
          color: #374151;
        }

        .btn-secondary:hover {
          background: #d1d5db;
        }
      `}</style>
    </div>
  )
}
