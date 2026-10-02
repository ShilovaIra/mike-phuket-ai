import { useEffect, useState } from 'react'
import { PlaceCategoryFormModal } from './PlaceCategoryFormModal'
import { placesApi } from '../places/placesApi'
import { placeCategoriesApi, type PlaceCategory } from './placeCategoriesApi'

export function PlaceCategoriesPage() {
  const [categories, setCategories] = useState<PlaceCategory[]>([])
  const [usedSlugs, setUsedSlugs] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<PlaceCategory | null>(null)
  const [creating, setCreating] = useState(false)

  async function reload() {
    const [loadedCategories, loadedPlaces] = await Promise.all([
      placeCategoriesApi.list(),
      placesApi.list(),
    ])
    setCategories(loadedCategories)
    setUsedSlugs(new Set(loadedPlaces.map((place) => place.category)))
  }

  async function remove(slug: string) {
    await placeCategoriesApi.remove(slug)
    await reload()
  }

  useEffect(() => {
    let cancelled = false
    reload().catch((err: Error) => {
      if (!cancelled) setError(err.message)
    })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Категории мест</h1>
        <button
          type="button"
          onClick={() => setCreating(true)}
          className="rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
        >
          Добавить категорию
        </button>
      </div>
      {error ? <p role="alert">{error}</p> : null}
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-slate-300">
            <th className="py-2 pr-4 font-medium">Slug</th>
            <th className="py-2 pr-4 font-medium">Название</th>
            <th className="py-2 pr-4 font-medium">Порядок</th>
            <th className="py-2 font-medium">Действия</th>
          </tr>
        </thead>
        <tbody>
          {categories.map((category) => (
            <tr key={category.slug} className="border-b border-slate-200">
              <td className="py-2 pr-4 font-mono">{category.slug}</td>
              <td className="py-2 pr-4">{category.label}</td>
              <td className="py-2 pr-4">{category.sort_order}</td>
              <td className="py-2">
                <button
                  type="button"
                  className="mr-3 text-slate-700 underline"
                  onClick={() => setEditing(category)}
                >
                  Изменить
                </button>
                {usedSlugs.has(category.slug) ? null : (
                  <button
                    type="button"
                    className="text-slate-700 underline"
                    onClick={() => void remove(category.slug)}
                  >
                    Удалить
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {creating ? (
        <PlaceCategoryFormModal
          onClose={() => setCreating(false)}
          onSaved={async () => {
            setCreating(false)
            await reload()
          }}
        />
      ) : null}
      {editing ? (
        <PlaceCategoryFormModal
          category={editing}
          onClose={() => setEditing(null)}
          onSaved={async () => {
            setEditing(null)
            await reload()
          }}
        />
      ) : null}
    </main>
  )
}
