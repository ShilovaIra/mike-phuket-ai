import { useEffect, useState } from 'react'
import { statsApi, type BotStats, type TopicStat } from './statsApi'

function topicRows(topics: TopicStat[]) {
  return [...topics].sort((a, b) => b.unique_users - a.unique_users)
}

function sourceRows(sources: Record<string, number>) {
  return Object.entries(sources).sort((a, b) => b[1] - a[1])
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
          <h2 className="mb-3 text-lg font-semibold">Темы (всё время)</h2>
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-slate-300">
                <th className="py-2 pr-4 font-medium">Тема</th>
                <th className="py-2 pr-4 font-medium">Пользователи</th>
                <th className="py-2 font-medium">Нажатия</th>
              </tr>
            </thead>
            <tbody>
              {topicRows(stats.topics_all_time).map((row) => (
                <tr key={`all-${row.slug}`} className="border-b border-slate-200">
                  <td className="py-2 pr-4">{row.label}</td>
                  <td className="py-2 pr-4">{row.unique_users}</td>
                  <td className="py-2">{row.taps}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <h2 className="mb-3 text-lg font-semibold">Темы (7 дней)</h2>
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-slate-300">
                <th className="py-2 pr-4 font-medium">Тема</th>
                <th className="py-2 pr-4 font-medium">Пользователи</th>
                <th className="py-2 font-medium">Нажатия</th>
              </tr>
            </thead>
            <tbody>
              {topicRows(stats.topics_7d).map((row) => (
                <tr key={`7d-${row.slug}`} className="border-b border-slate-200">
                  <td className="py-2 pr-4">{row.label}</td>
                  <td className="py-2 pr-4">{row.unique_users}</td>
                  <td className="py-2">{row.taps}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Источники пользователей</h2>
        <table className="w-full max-w-md border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-slate-300">
              <th className="py-2 pr-4 font-medium">Источник</th>
              <th className="py-2 font-medium">Пользователи</th>
            </tr>
          </thead>
          <tbody>
            {sourceRows(stats.users_by_first_source).map(([source, count]) => (
              <tr key={source} className="border-b border-slate-200">
                <td className="py-2 pr-4">{source}</td>
                <td className="py-2">{count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  )
}
