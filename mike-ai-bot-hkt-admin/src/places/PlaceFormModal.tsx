import { useEffect, useState, type FormEvent } from 'react'
import { partnersApi, type Partner } from '../partners/partnersApi'
import { placeCategoriesApi, type PlaceCategory } from '../place-categories/placeCategoriesApi'
import { placesApi, type PlaceInput } from './placesApi'

const emptyForm: PlaceInput = {
  name: '',
  category: '',
  blurb: '',
  maps_url: '',
  partner_id: null,
  is_active: true,
}

type Props = {
  onClose: () => void
  onSaved: () => void
}

export function PlaceFormModal({ onClose, onSaved }: Props) {
  const [form, setForm] = useState<PlaceInput>(emptyForm)
  const [categories, setCategories] = useState<PlaceCategory[]>([])
  const [partners, setPartners] = useState<Partner[]>([])
  const [error, setError] = useState<string | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    Promise.all([placeCategoriesApi.list(), partnersApi.list()])
      .then(([loadedCategories, loadedPartners]) => {
        if (cancelled) return
        setCategories(loadedCategories)
        setPartners(loadedPartners)
        setForm((prev) => ({
          ...prev,
          category: prev.category || loadedCategories[0]?.slug || '',
        }))
        setReady(true)
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message)
          setReady(true)
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  function setField<K extends keyof PlaceInput>(key: K, value: PlaceInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    try {
      await placesApi.create(form)
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить')
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/40 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Новое место"
        className="mt-8 w-full max-w-lg rounded-lg bg-white p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="mb-6 text-xl font-semibold tracking-tight">Новое место</h2>
        {!ready ? (
          <p>Загрузка…</p>
        ) : (
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <label className="flex flex-col gap-1 text-sm">
              Название
              <input
                value={form.name}
                onChange={(event) => setField('name', event.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Категория
              <select
                value={form.category}
                onChange={(event) => setField('category', event.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              >
                {categories.map((category) => (
                  <option key={category.slug} value={category.slug}>
                    {category.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Партнёр
              <select
                value={form.partner_id ?? ''}
                onChange={(event) => setField('partner_id', event.target.value || null)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
              >
                <option value="">Без партнёра</option>
                {partners.map((partner) => (
                  <option key={partner.id} value={partner.id}>
                    {partner.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Описание
              <textarea
                value={form.blurb}
                onChange={(event) => setField('blurb', event.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                rows={3}
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Ссылка на карту
              <input
                value={form.maps_url}
                onChange={(event) => setField('maps_url', event.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setField('is_active', event.target.checked)}
              />
              Активно
            </label>
            {error ? <p role="alert">{error}</p> : null}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded border border-slate-300 px-3 py-2 text-sm"
              >
                Отмена
              </button>
              <button type="submit" className="rounded bg-slate-900 px-3 py-2 text-sm text-white">
                Сохранить
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
