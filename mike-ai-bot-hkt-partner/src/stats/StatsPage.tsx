import { useEffect, useState } from 'react'
import { buildDonutSlices } from './buildDonutSlices'
import { ShareDonut } from './ShareDonut'
import { partnerApi, type PartnerRef, type PartnerStats } from './statsApi'

export function StatsPage() {
  const [partners, setPartners] = useState<PartnerRef[] | null>(null)
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [stats, setStats] = useState<PartnerStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    partnerApi
      .me()
      .then((me) => {
        if (cancelled) return
        setPartners(me.partners)
        setCurrentId(me.partners[0]?.id ?? null)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!currentId) {
      setStats(null)
      return
    }
    let cancelled = false
    partnerApi
      .stats(currentId)
      .then((data) => {
        if (!cancelled) setStats(data)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [currentId])

  if (error) {
    return (
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight">Статистика</h1>
        <p role="alert">{error}</p>
      </main>
    )
  }

  if (!partners) {
    return (
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight">Статистика</h1>
        <p>Загрузка…</p>
      </main>
    )
  }

  const current = partners.find((p) => p.id === currentId)
  const slices = stats
    ? buildDonutSlices([
        {
          key: 'opened',
          label: 'Показы с переходом',
          value: stats.all_time.opened_views,
        },
        {
          key: 'not_opened',
          label: 'Показы без перехода',
          value: stats.all_time.views - stats.all_time.opened_views,
        },
      ])
    : []

  return (
    <main className="mx-auto max-w-6xl space-y-10 px-4 py-8">
      <h1 className="text-2xl font-semibold tracking-tight">Статистика</h1>
      {partners.length > 1 ? (
        <label className="flex max-w-sm flex-col gap-1 text-sm">
          Партнёр
          <select
            value={currentId ?? ''}
            onChange={(e) => setCurrentId(e.target.value)}
            className="rounded border border-slate-300 bg-white px-3 py-2"
          >
            {partners.map((partner) => (
              <option key={partner.id} value={partner.id}>
                {partner.name}
              </option>
            ))}
          </select>
        </label>
      ) : current ? (
        <p className="text-slate-700">{current.name}</p>
      ) : null}

      {!stats ? (
        <p>Загрузка…</p>
      ) : (
        <div className="flex flex-col gap-8 md:flex-row md:items-center">
          <div className="min-w-0 flex-1 space-y-5">
            <section aria-label="В избранном и Открыто в Картах" className="grid gap-5 sm:grid-cols-2">
              <article className="rounded-lg border border-slate-200 bg-white p-6">
                <p className="text-sm text-slate-600">В избранном</p>
                <p className="mt-3 text-4xl font-semibold tracking-tight">{stats.favourite_users}</p>
              </article>
              <article className="rounded-lg border border-slate-200 bg-white p-6">
                <p className="text-sm text-slate-600">Открыто в Картах</p>
                <p className="mt-3 text-4xl font-semibold tracking-tight">{stats.map_opens}</p>
              </article>
            </section>
            <section aria-label="Пользователи категории" className="grid gap-5 sm:grid-cols-2">
              <article className="rounded-lg border border-slate-200 bg-white p-6">
                <p className="text-sm text-slate-600">
                  Пользователей, выбравших {stats.category_users.phrase} (всё время)
                </p>
                <p className="mt-3 text-4xl font-semibold tracking-tight">
                  {stats.category_users.all_time}
                </p>
              </article>
              <article className="rounded-lg border border-slate-200 bg-white p-6">
                <p className="text-sm text-slate-600">
                  Пользователей, выбравших {stats.category_users.phrase} (30 дней)
                </p>
                <p className="mt-3 text-4xl font-semibold tracking-tight">
                  {stats.category_users.last_30_days}
                </p>
              </article>
            </section>
            <section aria-label="За всё время" className="grid gap-5 sm:grid-cols-2">
              <article className="rounded-lg border border-slate-200 bg-white p-6">
                <p className="text-sm text-slate-600">Показы (всё время)</p>
                <p className="mt-3 text-4xl font-semibold tracking-tight">{stats.all_time.views}</p>
              </article>
              <article className="rounded-lg border border-slate-200 bg-white p-6">
                <p className="text-sm text-slate-600">Переходы (всё время)</p>
                <p className="mt-3 text-4xl font-semibold tracking-tight">{stats.all_time.referral_clicks}</p>
              </article>
            </section>
            <section aria-label="За 30 дней" className="grid gap-5 sm:grid-cols-2">
              <article className="rounded-lg border border-slate-200 bg-white p-6">
                <p className="text-sm text-slate-600">Показы (30 дней)</p>
                <p className="mt-3 text-4xl font-semibold tracking-tight">{stats.last_30_days.views}</p>
              </article>
              <article className="rounded-lg border border-slate-200 bg-white p-6">
                <p className="text-sm text-slate-600">Переходы (30 дней)</p>
                <p className="mt-3 text-4xl font-semibold tracking-tight">{stats.last_30_days.referral_clicks}</p>
              </article>
            </section>
          </div>
          <section
            aria-label="Показы с переходом и без"
            className="min-w-0 md:w-80 md:shrink-0"
          >
            <ShareDonut slices={slices} />
          </section>
        </div>
      )}
    </main>
  )
}
