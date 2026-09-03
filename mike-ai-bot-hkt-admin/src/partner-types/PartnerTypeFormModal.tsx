import { useEffect, useState, type FormEvent } from 'react'
import { partnerTypesApi, type PartnerType } from './partnerTypesApi'

const emptyForm: PartnerType = {
  slug: '',
  is_menu_visible: true,
  sort_order: 0,
  button_label: '',
  topic_label: '',
  intro: '',
  fallback: '',
  caption_emoji: '',
  caption_cta: '',
  button_template: '',
}

type Props = {
  mode: 'create' | 'edit'
  slug?: string
  onClose: () => void
  onSaved: () => void
}

export function PartnerTypeFormModal({ mode, slug: routeSlug, onClose, onSaved }: Props) {
  const [form, setForm] = useState<PartnerType>(emptyForm)
  const [error, setError] = useState<string | null>(null)
  const [ready, setReady] = useState(mode === 'create')

  useEffect(() => {
    if (mode !== 'edit' || !routeSlug) return
    let cancelled = false
    partnerTypesApi.get(routeSlug).then((existing) => {
      if (cancelled) return
      if (!existing) {
        setError('Тип партнёра не найден')
        setReady(true)
        return
      }
      setForm(existing)
      setReady(true)
    })
    return () => {
      cancelled = true
    }
  }, [mode, routeSlug])

  function setField<K extends keyof PartnerType>(key: K, value: PartnerType[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    try {
      if (mode === 'create') {
        await partnerTypesApi.create(form)
      } else if (routeSlug) {
        await partnerTypesApi.update(routeSlug, form)
      }
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
        aria-label={mode === 'create' ? 'Новый тип партнёра' : 'Изменить тип партнёра'}
        className="mt-8 w-full max-w-2xl rounded-lg bg-white p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-6 text-xl font-semibold tracking-tight">
          {mode === 'create' ? 'Новый тип партнёра' : 'Изменить тип партнёра'}
        </h2>
        {!ready ? (
          <p>Загрузка…</p>
        ) : mode === 'edit' && error === 'Тип партнёра не найден' ? (
          <p role="alert">{error}</p>
        ) : (
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <label className="flex flex-col gap-1 text-sm">
              Slug
              <input
                value={form.slug}
                onChange={(e) => setField('slug', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2 font-mono"
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Порядок
              <input
                type="number"
                value={form.sort_order}
                onChange={(e) => setField('sort_order', Number(e.target.value))}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_menu_visible}
                onChange={(e) => setField('is_menu_visible', e.target.checked)}
              />
              Видно в меню
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Кнопка меню
              <input
                value={form.button_label}
                onChange={(e) => setField('button_label', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Тема в статистике
              <input
                value={form.topic_label}
                onChange={(e) => setField('topic_label', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Intro
              <textarea
                value={form.intro}
                onChange={(e) => setField('intro', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                rows={2}
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Fallback
              <textarea
                value={form.fallback}
                onChange={(e) => setField('fallback', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                rows={2}
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Emoji подписи
              <input
                value={form.caption_emoji}
                onChange={(e) => setField('caption_emoji', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              CTA подписи
              <input
                value={form.caption_cta}
                onChange={(e) => setField('caption_cta', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Шаблон кнопки
              <input
                value={form.button_template}
                onChange={(e) => setField('button_template', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            {error && error !== 'Тип партнёра не найден' ? <p role="alert">{error}</p> : null}
            <div className="flex gap-3">
              <button
                type="submit"
                className="rounded bg-slate-900 px-4 py-2 text-white hover:bg-slate-800"
              >
                Сохранить
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded border border-slate-300 px-4 py-2 hover:bg-slate-50"
              >
                Отмена
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
