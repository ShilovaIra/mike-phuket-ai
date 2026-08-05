export type DonutInput = {
  key: string
  label: string
  value: number
}

export type DonutSlice = {
  key: string
  label: string
  value: number
  percent: number
}

const OTHER_KEY = 'other'
const OTHER_LABEL = 'Прочее'
const BUCKET_THRESHOLD = 0.05

export function buildDonutSlices(items: DonutInput[]): DonutSlice[] {
  const positive = items.filter((item) => item.value > 0)
  const total = positive.reduce((sum, item) => sum + item.value, 0)
  if (total === 0) return []

  const kept: DonutInput[] = []
  let otherValue = 0

  for (const item of positive) {
    if (item.value / total < BUCKET_THRESHOLD) {
      otherValue += item.value
    } else {
      kept.push(item)
    }
  }

  const merged = [...kept]
  if (otherValue > 0) {
    merged.push({ key: OTHER_KEY, label: OTHER_LABEL, value: otherValue })
  }

  merged.sort((a, b) => {
    if (a.key === OTHER_KEY) return 1
    if (b.key === OTHER_KEY) return -1
    return b.value - a.value
  })

  const percents = allocatePercents(merged.map((item) => item.value), total)

  return merged.map((item, index) => ({
    key: item.key,
    label: item.label,
    value: item.value,
    percent: percents[index]!,
  }))
}

/** Largest-remainder method so whole percents sum to 100. */
function allocatePercents(values: number[], total: number): number[] {
  const exact = values.map((value) => (value / total) * 100)
  const floored = exact.map((p) => Math.floor(p))
  let remaining = 100 - floored.reduce((sum, p) => sum + p, 0)

  const order = exact
    .map((p, index) => ({ index, frac: p - Math.floor(p) }))
    .sort((a, b) => b.frac - a.frac)

  const result = [...floored]
  for (const { index } of order) {
    if (remaining <= 0) break
    result[index]! += 1
    remaining -= 1
  }
  return result
}
