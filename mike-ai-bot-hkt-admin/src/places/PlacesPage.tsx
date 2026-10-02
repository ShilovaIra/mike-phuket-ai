import { useEffect, useState } from 'react'
import { placeCategoriesApi, type PlaceCategory } from '../place-categories/placeCategoriesApi'
import placeholder from '../assets/placeholders/empty_picture_placeholder.jpg'
import { PlaceFormModal } from './PlaceFormModal'
import { placesApi, type Place } from './placesApi'

export function PlacesPage() {
  const [places, setPlaces] = useState<Place[]>([])
  const [categories, setCategories] = useState<PlaceCategory[]>([])
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<Place | null>(null)

  async function reload() {
    const [loadedPlaces, loadedCategories] = await Promise.all([
      placesApi.list(),
      placeCategoriesApi.list(),
    ])
    setPlaces(loadedPlaces)
    setCategories(loadedCategories)
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

  const labelFor = (slug: string) => categories.find((category) => category.slug === slug)?.label ?? slug

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Места</h1>
        <button
          type="button"
          onClick={() => setCreating(true)}
          className="rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
        >
          Добавить место
        </button>
      </div>
      {error ? <p role="alert">{error}</p> : null}
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-slate-300">
            <th className="py-2 pr-4 font-medium">Фото</th>
            <th className="py-2 pr-4 font-medium">Название</th>
            <th className="py-2 pr-4 font-medium">Категория</th>
            <th className="py-2 pr-4 font-medium">Описание</th>
            <th className="py-2 pr-4 font-medium">Активно</th>
            <th className="py-2 pr-4 font-medium">Майк рекомендует</th>
            <th className="py-2 font-medium">Действия</th>
          </tr>
        </thead>
        <tbody>
          {places.map((place) => (
            <tr key={place.id} className="border-b border-slate-200">
              <td className="py-2 pr-4">
                <img
                  src={place.photos[0]?.url || placeholder}
                  alt={`Фото ${place.name}`}
                  className="h-8 w-8 rounded object-cover"
                />
              </td>
              <td className="py-2 pr-4">{place.name}</td>
              <td className="py-2 pr-4">{labelFor(place.category)}</td>
              <td className="py-2 pr-4">{place.blurb}</td>
              <td className="py-2 pr-4">{place.is_active ? 'да' : 'нет'}</td>
              <td className="py-2 pr-4">{place.mike_recommends ? 'да' : 'нет'}</td>
              <td className="py-2">
                <button
                  type="button"
                  className="text-slate-700 underline hover:text-slate-900"
                  onClick={() => setEditing(place)}
                >
                  Изменить
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {creating ? (
        <PlaceFormModal
          onClose={() => setCreating(false)}
          onChanged={reload}
          onSaved={async () => {
            setCreating(false)
            await reload()
          }}
        />
      ) : null}
      {editing ? (
        <PlaceFormModal
          place={editing}
          onClose={() => setEditing(null)}
          onChanged={reload}
          onSaved={async () => {
            setEditing(null)
            await reload()
          }}
        />
      ) : null}
    </main>
  )
}
