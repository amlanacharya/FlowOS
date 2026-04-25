import { useEffect, useRef, useState } from 'react'
import jsQR from 'jsqr'
import { QrCheckinResponse } from '../types'

type PushNoticeFn = (tone: 'success' | 'error' | 'info' | 'warning', message: string) => void

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
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState<QrCheckinResponse | null>(null)
  const [manualCode, setManualCode] = useState('')
  const [cameraError, setCameraError] = useState<string>('')
  const scanningRef = useRef(false)

  // Start camera
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
        scanningRef.current = true
        scanQR()
      } catch (err) {
        setCameraError('Camera access denied or unavailable')
      }
    }

    startCamera()

    return () => {
      // Cleanup: stop tracks and close modal
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      scanningRef.current = false
    }
  }, [open])

  // QR scanning loop
  const scanQR = () => {
    if (!scanningRef.current || !videoRef.current || !canvasRef.current) return

    const canvas = canvasRef.current
    const video = videoRef.current
    const ctx = canvas.getContext('2d')

    if (video.readyState !== video.HAVE_ENOUGH_DATA || !ctx) {
      requestAnimationFrame(scanQR)
      return
    }

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    ctx.drawImage(video, 0, 0)

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const code = jsQR(imageData.data, canvas.width, canvas.height)

    if (code) {
      handleScan(code.data)
    } else {
      requestAnimationFrame(scanQR)
    }
  }

  const handleScan = async (memberCode: string) => {
    if (loading || success) return
    scanningRef.current = false

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
        pushNotice('error', data.detail || 'Check-in failed')
        scanningRef.current = true
        scanQR()
      } else {
        setSuccess(data)
        pushNotice('success', `${data.member_name} checked in`)
        setTimeout(() => {
          setSuccess(null)
          scanningRef.current = true
          scanQR()
        }, 3000)
      }
    } catch (err) {
      pushNotice('error', 'Network error during check-in')
      scanningRef.current = true
      scanQR()
    } finally {
      setLoading(false)
    }
  }

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (manualCode.trim()) {
      setManualCode('')
      handleScan(manualCode.trim())
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
                }}
              />
              <canvas ref={canvasRef} style={{ display: 'none' }} />

              {success && (
                <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✓</div>
                  <h3>{success.member_name}</h3>
                  {success.subscription_end_date && (
                    <p style={{ color: '#666', marginBottom: '0.5rem' }}>
                      Expires: {new Date(success.subscription_end_date).toLocaleDateString()}
                    </p>
                  )}
                  {success.amount_due > 0 && (
                    <p style={{ color: '#d32f2f', fontWeight: 'bold' }}>
                      Amount Due: ₹{success.amount_due.toFixed(2)}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Manual entry fallback */}
          <form onSubmit={handleManualSubmit}>
            <label>
              <div style={{ fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                Or enter member code manually:
              </div>
              <input
                type="text"
                placeholder="Member code"
                value={manualCode}
                onChange={e => setManualCode(e.target.value)}
                style={{ marginBottom: '0.5rem' }}
                disabled={loading}
              />
            </label>
            <button type="submit" className="btn btn-primary" disabled={loading || !manualCode.trim()}>
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
      `}</style>
    </div>
  )
}
