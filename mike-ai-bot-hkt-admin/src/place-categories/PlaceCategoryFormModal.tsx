import { useState, type FormEvent } from 'react'
import {
  placeCategoriesApi,
  type PlaceCategory,
  type PlaceCategoryInput,
} from './placeCategoriesApi'

const emptyForm: PlaceCategoryInput = {
  slug: '',
  label: '',
  sort_order: 0,
}

type Props = {
  category?: PlaceCategory
  onClose: () => void
  onSaved: () => void
}

export function PlaceCategoryFormModal({ category, onClose, onSaved }: Props) {
  const [form, setForm] = useState<PlaceCategoryInput>(
    category
      ? { slug: category.slug, label: category.label, sort_order: category.sort_order }
      : emptyForm,
  )
  const [error, setError] = useState<string | null>(null)

  function setField<K extends keyof PlaceCategoryInput>(key: K, value: PlaceCategoryInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    try {
      if (category) {
        await placeCategoriesApi.update(category.slug, {
          label: form.label,
          sort_order: form.sort_order,
        })
      } else {
        await placeCategoriesApi.create(form)
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
        aria-label={category ? 'Изменить категорию' : 'Новая категория'}
        className="mt-8 w-full max-w-lg rounded-lg bg-white p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="mb-6 text-xl font-semibold tracking-tight">
          {category ? 'Изменить категорию' : 'Новая категория'}
        </h2>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1 text-sm">
            Slug
            <input
              value={form.slug}
              onChange={(event) => setField('slug', event.target.value)}
              className="rounded border border-slate-300 bg-white px-3 py-2 font-mono"
              required
              disabled={category != null}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Название
            <input
              value={form.label}
              onChange={(event) => setField('label', event.target.value)}
              className="rounded border border-slate-300 bg-white px-3 py-2"
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Порядок
            <input
              type="number"
              value={form.sort_order}
              onChange={(event) => setField('sort_order', Number(event.target.value))}
              className="rounded border border-slate-300 bg-white px-3 py-2"
              required
            />
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
      </div>
    </div>
  )
}
