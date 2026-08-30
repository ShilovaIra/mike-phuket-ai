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
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight">Статистика</h1>
        <p role="alert">{error}</p>
      </main>
    )
  }

  if (!partners) {
    return (
      <main className="mx-auto max-w-5xl px-4 py-8">
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
          label: 'Открытые показы',
          value: stats.all_time.opened_views,
        },
        {
          key: 'not_opened',
          label: 'Без перехода',
          value: stats.all_time.views - stats.all_time.opened_views,
        },
      ])
    : []

  return (
    <main className="mx-auto max-w-5xl space-y-10 px-4 py-8">
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
        <>
          <section aria-label="За всё время" className="grid gap-4 sm:grid-cols-3">
            <article className="rounded border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-600">Показы (всё время)</p>
              <p className="text-2xl font-semibold">{stats.all_time.views}</p>
            </article>
            <article className="rounded border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-600">Переходы (всё время)</p>
              <p className="text-2xl font-semibold">{stats.all_time.referral_clicks}</p>
            </article>
            <article className="rounded border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-600">Открытые показы (всё время)</p>
              <p className="text-2xl font-semibold">{stats.all_time.opened_views}</p>
            </article>
          </section>
          <section aria-label="За 30 дней" className="grid gap-4 sm:grid-cols-3">
            <article className="rounded border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-600">Показы (30 дней)</p>
              <p className="text-2xl font-semibold">{stats.last_30_days.views}</p>
            </article>
            <article className="rounded border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-600">Переходы (30 дней)</p>
              <p className="text-2xl font-semibold">{stats.last_30_days.referral_clicks}</p>
            </article>
            <article className="rounded border border-slate-200 bg-white p-4">
              <p className="text-sm text-slate-600">Открытые показы (30 дней)</p>
              <p className="text-2xl font-semibold">{stats.last_30_days.opened_views}</p>
            </article>
          </section>
          <section>
            <h2 className="mb-3 text-lg font-semibold">Показы: переход или нет</h2>
            <ShareDonut slices={slices} />
          </section>
        </>
      )}
    </main>
  )
}
