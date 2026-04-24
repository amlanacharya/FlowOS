type Props = {
  variant?: 'text' | 'title' | 'kpi' | 'chart'
  width?: string
  style?: React.CSSProperties
}

export default function Skeleton({ variant = 'text', width, style }: Props) {
  return (
    <div
      className={`skeleton skeleton-${variant}`}
      style={{ width: width ?? '100%', ...style }}
    />
  )
}

export function SkeletonKpiGrid() {
  return (
    <div className="kpi-grid">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} variant="kpi" />
      ))}
    </div>
  )
}

export function SkeletonTableRows({ count = 6 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <tr key={i}>
          <td colSpan={10} style={{ padding: '8px 16px' }}>
            <Skeleton variant="text" style={{ height: 20 }} />
          </td>
        </tr>
      ))}
    </>
  )
}
