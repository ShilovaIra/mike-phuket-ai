import { useEffect, useState } from 'react'
import { buildDonutSlices } from './buildDonutSlices'
import { ShareDonut } from './ShareDonut'
import { statsApi, type BotStats } from './statsApi'
import { sourceLabel } from './sourceLabel'
import { stripLeadingEmoji } from './stripLeadingEmoji'

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
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight">Статистика</h1>
        <p role="alert">{error}</p>
      </main>
    )
  }

  if (!stats) {
    return (
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight">Статистика</h1>
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

  return (
    <main className="mx-auto max-w-5xl space-y-10 px-4 py-8">
      <h1 className="text-2xl font-semibold tracking-tight">Статистика</h1>

      <section aria-label="Ключевые показатели" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <article className="rounded border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-600">Всего пользователей</p>
          <p className="text-2xl font-semibold">{stats.total_users}</p>
        </article>
        <article className="rounded border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-600">Новые сегодня</p>
          <p className="text-2xl font-semibold">{stats.new_users_today}</p>
        </article>
        <article className="rounded border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-600">Активны сегодня</p>
          <p className="text-2xl font-semibold">{stats.active_today}</p>
        </article>
        <article className="rounded border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-600">Лиды (всего)</p>
          <p className="text-2xl font-semibold">{stats.leads_all_time}</p>
        </article>
        <article className="rounded border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-600">Новые за 7 дней</p>
          <p className="text-2xl font-semibold">{stats.new_users_7d}</p>
        </article>
        <article className="rounded border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-600">Лиды (7 дней)</p>
          <p className="text-2xl font-semibold">{stats.leads_7d}</p>
        </article>
      </section>

      <section className="grid gap-8 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 text-lg font-semibold">Популярные темы</h2>
          <ShareDonut slices={topicSlices} />
        </div>
        <div>
          <h2 className="mb-3 text-lg font-semibold">Источники пользователей</h2>
          <ShareDonut slices={sourceSlices} />
        </div>
      </section>
    </main>
  )
}
