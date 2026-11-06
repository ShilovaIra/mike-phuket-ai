import { useEffect, useState } from 'react'
import { ActivityChart } from './ActivityChart'
import { buildDonutSlices } from './buildDonutSlices'
import { ShareDonut } from './ShareDonut'
import { statsApi, type BotStats } from './statsApi'
import { sourceLabel } from './sourceLabel'
import { stripLeadingEmoji } from './stripLeadingEmoji'
import { Icon, type IconName } from '../shell/icons'

const CARDS: Array<{
  key: keyof BotStats['deltas']
  label: string
  icon: IconName
  value: (stats: BotStats) => number
}> = [
  { key: 'total_users', label: 'Всего пользователей', icon: 'users', value: (stats) => stats.total_users },
  { key: 'new_users_today', label: 'Новые сегодня', icon: 'user', value: (stats) => stats.new_users_today },
  { key: 'active_today', label: 'Активные сегодня', icon: 'pulse', value: (stats) => stats.active_today },
  { key: 'leads_all_time', label: 'Лиды (всего)', icon: 'funnel', value: (stats) => stats.leads_all_time },
  { key: 'new_users_7d', label: 'Новые за 7 дней', icon: 'calendar', value: (stats) => stats.new_users_7d },
  { key: 'leads_7d', label: 'Лиды (7 дней)', icon: 'users', value: (stats) => stats.leads_7d },
]

function deltaText(value: number): string {
  if (value > 0) return `+${value}%`
  return `${value}%`
}

function deltaTone(value: number): string {
  if (value > 0) return 'is-up'
  if (value < 0) return 'is-down'
  return 'is-flat'
}

function usersWord(count: number): string {
  const n = Math.abs(count) % 100
  const last = n % 10
  if (n > 10 && n < 20) return 'пользователей'
  if (last === 1) return 'пользователь'
  if (last >= 2 && last <= 4) return 'пользователя'
  return 'пользователей'
}

export function StatsPage() {
  const [stats, setStats] = useState<BotStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    statsApi
      .get()
      .then((data) => {
        if (!cancelled) setStats(data)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (error) {
    return (
      <main className="stat-page">
        <header className="stat-head">
          <h1>Статистика</h1>
        </header>
        <p role="alert">{error}</p>
      </main>
    )
  }

  if (!stats) {
    return (
      <main className="stat-page">
        <header className="stat-head">
          <h1>Статистика</h1>
        </header>
        <p>Загрузка…</p>
      </main>
    )
  }

  const topicSlices = buildDonutSlices(
    stats.topics_all_time.map((topic) => ({
      key: topic.slug,
      label: stripLeadingEmoji(topic.label),
      value: topic.unique_users,
    })),
  )
  const sourceSlices = buildDonutSlices(
    Object.entries(stats.users_by_first_source).map(([key, value]) => ({
      key,
      label: sourceLabel(key),
      value,
    })),
  )
  const sourceTotal = sourceSlices.reduce((sum, slice) => sum + slice.value, 0)

  return (
    <main className="stat-page">
      <header className="stat-head">
        <h1>Статистика</h1>
        <p>Обзор активности пользователей и ключевых показателей</p>
      </header>

      <section aria-label="Ключевые показатели" className="stat-kpis">
        {CARDS.map((card) => {
          const change = stats.deltas?.[card.key] ?? 0
          return (
            <article key={card.key} className="stat-card">
              <div className="stat-card-top">
                <span className="stat-icon">
                  <Icon name={card.icon} />
                </span>
                <p className="stat-label">{card.label}</p>
              </div>
              <div className="stat-card-bottom">
                <p className="stat-value">{card.value(stats)}</p>
                <p className={`delta ${deltaTone(change)}`}>
                  {change !== 0 && (
                    <svg viewBox="0 0 12 12" aria-hidden="true">
                      <path d={change > 0 ? 'M6 2.2 10.2 8H1.8Z' : 'M6 9.8 1.8 4h8.4Z'} fill="currentColor" />
                    </svg>
                  )}
                  {deltaText(change)}
                </p>
              </div>
            </article>
          )
        })}
      </section>

      <section className="stat-panels">
        <div className="stat-panel">
          <h2>Популярные темы</h2>
          <ShareDonut
            slices={topicSlices}
            centerValue={topicSlices.length > 0 ? '100%' : undefined}
            centerLabel="запросов"
          />
        </div>
        <div className="stat-panel">
          <h2>Источники пользователей</h2>
          <ShareDonut
            slices={sourceSlices}
            centerValue={sourceSlices.length > 0 ? String(sourceTotal) : undefined}
            centerLabel={usersWord(sourceTotal)}
          />
        </div>
      </section>

      <section className="stat-panel" aria-label="Динамика активности">
        <h2>Динамика активности</h2>
        <ActivityChart points={stats.activity ?? []} />
      </section>
    </main>
  )
}
