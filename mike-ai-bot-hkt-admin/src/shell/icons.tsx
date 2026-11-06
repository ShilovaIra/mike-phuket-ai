import type { ReactNode } from 'react'

type IconName =
  | 'spark'
  | 'chart'
  | 'send'
  | 'users'
  | 'tag'
  | 'pin'
  | 'book'
  | 'layers'
  | 'idcard'
  | 'calendar'
  | 'clock'
  | 'check'
  | 'link'
  | 'plus'
  | 'search'
  | 'pencil'
  | 'trash'
  | 'play'
  | 'chevronUp'
  | 'chevronDown'
  | 'chevronLeft'
  | 'chevronRight'
  | 'dots'

const paths: Record<Exclude<IconName, 'spark'>, ReactNode> = {
  chart: (
    <>
      <path d="M4 19V5" />
      <path d="M4 19h16" />
      <path d="M8 16v-4" />
      <path d="M12 16V8" />
      <path d="M16 16v-6" />
    </>
  ),
  send: (
    <>
      <path d="M4 12 20 4l-6 16-2.2-6.2L4 12Z" />
      <path d="M11.6 13.6 20 4" />
    </>
  ),
  users: (
    <>
      <circle cx="9" cy="9" r="3" />
      <path d="M3.5 19c.6-2.6 2.8-4 5.5-4s4.9 1.4 5.5 4" />
      <circle cx="17" cy="9.5" r="2.2" />
      <path d="M16.2 15.2c1.8.3 3.2 1.4 3.8 3.3" />
    </>
  ),
  tag: (
    <>
      <path d="M20 13.2 12.8 20a2 2 0 0 1-2.8 0L3 13V3h10l7 7.2a2 2 0 0 1 0 2.8Z" />
      <circle cx="7.5" cy="7.5" r="1" />
    </>
  ),
  pin: (
    <>
      <path d="M12 21s7-6.1 7-11a7 7 0 1 0-14 0c0 4.9 7 11 7 11Z" />
      <circle cx="12" cy="10" r="2.2" />
    </>
  ),
  book: (
    <>
      <path d="M5 4.5h11a3 3 0 0 1 3 3V20H8a3 3 0 0 0-3 3" />
      <path d="M5 4.5A3 3 0 0 0 2 7.5V20a3 3 0 0 1 3-3h14" />
    </>
  ),
  layers: (
    <>
      <path d="m12 3 9 5-9 5L3 8l9-5Z" />
      <path d="m3 12 9 5 9-5" />
      <path d="m3 16 9 5 9-5" />
    </>
  ),
  idcard: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <circle cx="9" cy="12" r="2" />
      <path d="M14 10h4" />
      <path d="M14 14h4" />
    </>
  ),
  calendar: (
    <>
      <rect x="3.5" y="5" width="17" height="15" rx="2" />
      <path d="M8 3.5V7" />
      <path d="M16 3.5V7" />
      <path d="M3.5 10h17" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v4.5l3 2" />
    </>
  ),
  check: (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="m8.5 12.2 2.4 2.4 4.6-5" />
    </>
  ),
  link: (
    <>
      <path d="M10 13a5 5 0 0 0 7.1.1l1.4-1.5a5 5 0 0 0-7-7.1L10.2 6" />
      <path d="M14 11a5 5 0 0 0-7.1-.1L5.5 12.4a5 5 0 0 0 7 7.1L14 18" />
    </>
  ),
  plus: (
    <>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m16 16 4 4" />
    </>
  ),
  pencil: (
    <>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z" />
    </>
  ),
  trash: (
    <>
      <path d="M4 7h16" />
      <path d="M9 7V5h6v2" />
      <path d="M7 7l1 13h8l1-13" />
    </>
  ),
  play: <path d="m8 6 10 6-10 6V6Z" />,
  chevronUp: <path d="m6 14 6-6 6 6" />,
  chevronDown: <path d="m6 10 6 6 6-6" />,
  chevronLeft: <path d="m14 6-6 6 6 6" />,
  chevronRight: <path d="m10 6 6 6-6 6" />,
  dots: (
    <>
      <circle cx="6" cy="12" r="1.25" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.25" fill="currentColor" stroke="none" />
      <circle cx="18" cy="12" r="1.25" fill="currentColor" stroke="none" />
    </>
  ),
}

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  if (name === 'spark') {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
        <path
          fill="currentColor"
          d="M12 1.6 13.9 8.4 20.8 10.1 13.9 11.8 12 18.6 10.1 11.8 3.2 10.1 10.1 8.4Z"
        />
      </svg>
    )
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  )
}
