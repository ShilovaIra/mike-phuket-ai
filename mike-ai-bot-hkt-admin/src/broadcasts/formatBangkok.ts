const MONTHS = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']

export function formatBangkok(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Bangkok',
    day: 'numeric',
    month: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(date)
  const pick = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((part) => part.type === type)?.value ?? ''
  const month = MONTHS[Number(pick('month')) - 1] ?? ''
  return `${Number(pick('day'))} ${month}, ${pick('hour')}:${pick('minute')}`
}

export function daysLabel(count: number): string {
  const n = Math.abs(Math.trunc(count)) % 100
  const last = n % 10
  if (n > 10 && n < 20) return 'дней'
  if (last === 1) return 'день'
  if (last >= 2 && last <= 4) return 'дня'
  return 'дней'
}

export function chainDelay(index: number, intervalDays: number | null): string {
  if (intervalDays == null || intervalDays < 1) return 'По порядку'
  if (index === 0) return 'Сразу'
  const days = index * intervalDays
  return `Через ${days} ${daysLabel(days)}`
}
