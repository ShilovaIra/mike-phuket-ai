import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { DonutSlice } from './buildDonutSlices'

const PALETTE = ['#3B82F6', '#22D3EE', '#22C55E', '#15803D', '#8B5CF6', '#EC4899']
const OTHER_COLOR = '#F59E0B'

type ShareDonutProps = {
  slices: DonutSlice[]
}

function sliceColor(slice: DonutSlice, index: number): string {
  if (slice.key === 'other') return OTHER_COLOR
  return PALETTE[index % PALETTE.length]!
}

function ShareTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ payload: DonutSlice }>
}) {
  if (!active || !payload?.[0]) return null
  const slice = payload[0].payload
  return (
    <div className="rounded border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm">
      {slice.label}: {slice.value}
    </div>
  )
}

export function ShareDonut({ slices }: ShareDonutProps) {
  if (slices.length === 0) {
    return <p className="text-sm text-slate-600">Пока нет данных</p>
  }

  const colored = slices.map((slice, index) => ({
    ...slice,
    fill: sliceColor(slice, index),
  }))

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="h-44 w-44 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={colored}
              dataKey="value"
              nameKey="label"
              cx="50%"
              cy="50%"
              innerRadius="58%"
              outerRadius="88%"
              paddingAngle={1}
              stroke="none"
            >
              {colored.map((slice) => (
                <Cell key={slice.key} fill={slice.fill} />
              ))}
            </Pie>
            <Tooltip content={<ShareTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="w-full min-w-0 space-y-2 text-sm">
        {colored.map((slice) => (
          <li key={slice.key} className="flex items-center justify-between gap-3">
            <span className="flex min-w-0 items-center gap-2">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: slice.fill }}
                aria-hidden
              />
              <span className="truncate">{slice.label}</span>
            </span>
            <span className="shrink-0 tabular-nums text-slate-700">{slice.percent}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
