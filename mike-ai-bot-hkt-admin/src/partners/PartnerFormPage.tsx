import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { partnerTypesApi, type PartnerType } from '../partner-types/partnerTypesApi'
import { partnersApi, type PartnerInput } from './partnersApi'

const emptyForm: PartnerInput = {
  name: '',
  type: '',
  referral_url: '',
  blurb: '',
  is_active: true,
  sort_order: 0,
}

type Props = {
  mode: 'create' | 'edit'
}

export function PartnerFormPage({ mode }: Props) {
  const navigate = useNavigate()
  const { id } = useParams()
  const [typeOptions, setTypeOptions] = useState<PartnerType[]>([])
  const [form, setForm] = useState<PartnerInput>(emptyForm)
  const [error, setError] = useState<string | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const types = await partnerTypesApi.list()
      if (cancelled) return
      setTypeOptions(types)

      if (mode === 'edit' && id) {
        const existing = await partnersApi.get(id)
        if (cancelled) return
        if (!existing) {
          setError('Партнёр не найден')
          setReady(true)
          return
        }
        setForm({
          name: existing.name,
          type: existing.type,
          referral_url: existing.referral_url,
          blurb: existing.blurb,
          is_active: existing.is_active,
          sort_order: existing.sort_order,
        })
      } else {
        setForm({ ...emptyForm, type: types[0]?.slug ?? '' })
      }
      setReady(true)
    })().catch((err: Error) => {
      if (!cancelled) {
        setError(err.message)
        setReady(true)
      }
    })
    return () => {
      cancelled = true
    }
  }, [mode, id])

  function setField<K extends keyof PartnerInput>(key: K, value: PartnerInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    try {
      if (mode === 'create') {
        await partnersApi.create(form)
      } else if (id) {
        await partnersApi.update(id, form)
      }
      navigate('/partners', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить')
    }
  }

  if (!ready) {
    return <main className="mx-auto max-w-2xl px-4 py-8">Загрузка…</main>
  }

  if (error === 'Партнёр не найден') {
    return (
      <main className="mx-auto max-w-2xl px-4 py-8">
        <p role="alert">{error}</p>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">
        {mode === 'create' ? 'Новый партнёр' : 'Изменить партнёра'}
      </h1>
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Имя
          <input
            value={form.name}
            onChange={(e) => setField('name', e.target.value)}
            className="rounded border border-slate-300 bg-white px-3 py-2"
            required
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Тип
          <select
            value={form.type}
            onChange={(e) => setField('type', e.target.value)}
            className="rounded border border-slate-300 bg-white px-3 py-2"
            required
          >
            {typeOptions.map((type) => (
              <option key={type.slug} value={type.slug}>
                {type.slug}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Referral URL
          <input
            type="url"
            value={form.referral_url}
            onChange={(e) => setField('referral_url', e.target.value)}
            className="rounded border border-slate-300 bg-white px-3 py-2"
            required
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Описание
          <textarea
            value={form.blurb}
            onChange={(e) => setField('blurb', e.target.value)}
            className="rounded border border-slate-300 bg-white px-3 py-2"
            rows={3}
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
            checked={form.is_active}
            onChange={(e) => setField('is_active', e.target.checked)}
          />
          Активен
        </label>
        {error && error !== 'Партнёр не найден' ? <p role="alert">{error}</p> : null}
        <button
          type="submit"
          className="rounded bg-slate-900 px-4 py-2 text-white hover:bg-slate-800"
        >
          Сохранить
        </button>
      </form>
    </main>
  )
}
