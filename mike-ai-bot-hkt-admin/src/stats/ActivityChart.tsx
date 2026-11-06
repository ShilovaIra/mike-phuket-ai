import type { ActivityPoint } from './statsApi'

const MONTHS = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']

export function formatActivityDay(iso: string): string {
  const [, month, day] = iso.split('-').map(Number)
  return `${day} ${MONTHS[(month ?? 1) - 1]}`
}

export function ActivityChart({ points }: { points: ActivityPoint[] }) {
  const width = 640
  const height = 168
  const padX = 12
  const padY = 16
  const max = Math.max(1, ...points.map((point) => point.active_users), 0)
  const step = points.length > 1 ? (width - padX * 2) / (points.length - 1) : 0
  const coords = points.map((point, index) => {
    const x = padX + index * step
    const y = height - padY - (point.active_users / max) * (height - padY * 2)
    return { x, y }
  })
  const line = coords.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ')
  const area =
    coords.length > 0
      ? `${line} L ${coords[coords.length - 1]!.x} ${height - 8} L ${coords[0]!.x} ${height - 8} Z`
      : ''

  return (
    <div className="activity-chart">
      <svg viewBox={`0 0 ${width} ${height}`} className="activity-line" aria-hidden="true">
        <defs>
          <linearGradient id="activity-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#8b7cff" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#8b7cff" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75, 1].map((mark) => {
          const y = height - padY - mark * (height - padY * 2)
          return <line key={mark} x1={padX} x2={width - padX} y1={y} y2={y} className="activity-grid" />
        })}
        {area && <path d={area} fill="url(#activity-fill)" />}
        {line && <path d={line} className="activity-stroke" />}
        {coords.map((point, index) => (
          <circle key={points[index]!.date} cx={point.x} cy={point.y} r="4" className="activity-dot" />
        ))}
      </svg>
      <ol className="activity-axis">
        {points.map((point) => (
          <li key={point.date}>
            <time dateTime={point.date}>{formatActivityDay(point.date)}</time>
            <span className="activity-count">{point.active_users}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}
