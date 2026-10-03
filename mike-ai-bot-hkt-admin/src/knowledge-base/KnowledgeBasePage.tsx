import { useEffect, useState, type FormEvent } from 'react'
import { partnerTypesApi, type PartnerType } from '../partner-types/partnerTypesApi'
import { partnersApi, type Partner } from '../partners/partnersApi'
import { placeCategoriesApi, type PlaceCategory } from '../place-categories/placeCategoriesApi'
import { placesApi, type Place } from '../places/placesApi'
import { knowledgeBaseApi, type KnowledgeBaseEntry } from './knowledgeBaseApi'

type Choice = { value: string; label: string }

function addableChoices(
  entries: KnowledgeBaseEntry[],
  partners: Partner[],
  types: PartnerType[],
  places: Place[],
  categories: PlaceCategory[],
): Choice[] {
  const partnerIds = new Set(entries.flatMap((entry) => (entry.partner_id ? [entry.partner_id] : [])))
  const placeIds = new Set(entries.flatMap((entry) => (entry.place_id ? [entry.place_id] : [])))
  for (const place of places) {
    if (placeIds.has(place.id) && place.partner_id) partnerIds.add(place.partner_id)
  }
  const typeLabel = Object.fromEntries(types.map((type) => [type.slug, type.topic_label]))
  const categoryLabel = Object.fromEntries(categories.map((category) => [category.slug, category.label]))
  const partnerChoices = partners
    .filter((partner) => !partnerIds.has(partner.id))
    .map((partner) => ({
      value: `partner:${partner.id}`,
      label: `${partner.name} (${typeLabel[partner.type] ?? partner.type})`,
    }))
  const placeChoices = places
    .filter((place) => !placeIds.has(place.id))
    .filter((place) => !place.partner_id || !partnerIds.has(place.partner_id))
    .map((place) => ({
      value: `place:${place.id}`,
      label: `${place.name} (${categoryLabel[place.category] ?? place.category})`,
    }))
  return [...partnerChoices, ...placeChoices]
}

export function KnowledgeBasePage() {
  const [entries, setEntries] = useState<KnowledgeBaseEntry[]>([])
  const [choices, setChoices] = useState<Choice[]>([])
  const [error, setError] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)
  const [ready, setReady] = useState(false)

  async function reload() {
    const [nextEntries, partners, types, places, categories] = await Promise.all([
      knowledgeBaseApi.list(),
      partnersApi.list(),
      partnerTypesApi.list(),
      placesApi.list(),
      placeCategoriesApi.list(),
    ])
    setEntries(nextEntries)
    setChoices(addableChoices(nextEntries, partners, types, places, categories))
    setReady(true)
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
        <h1 className="text-2xl font-semibold tracking-tight">База знаний</h1>
        {ready ? (
          <button
            type="button"
            onClick={() => setAdding(true)}
            className="rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
          >
            Добавить
          </button>
        ) : null}
      </div>
      {error ? <p role="alert">{error}</p> : null}
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-slate-300">
            <th className="py-2 pr-4 font-medium">Имя</th>
            <th className="py-2 pr-4 font-medium">Вид</th>
            <th className="py-2 pr-4 font-medium">Ссылка</th>
            <th className="py-2 pr-4 font-medium">В чате</th>
            <th className="py-2 font-medium">Действия</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.id} className="border-b border-slate-200">
              <td className="py-2 pr-4">{entry.name}</td>
              <td className="py-2 pr-4">{entry.kind}</td>
              <td className="py-2 pr-4">
                {[entry.referral_url, entry.maps_url].filter(Boolean).join(' ')}
              </td>
              <td className="py-2 pr-4">В чате: {entry.in_chat ? 'да' : 'нет'}</td>
              <td className="py-2">
                <button
                  type="button"
                  className="text-slate-700 underline hover:text-slate-900"
                  onClick={async () => {
                    await knowledgeBaseApi.remove(entry.id)
                    await reload()
                  }}
                >
                  Удалить
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {adding ? (
        <AddDialog
          choices={choices}
          onClose={() => setAdding(false)}
          onSaved={async () => {
            setAdding(false)
            await reload()
          }}
        />
      ) : null}
    </main>
  )
}

function AddDialog({
  choices,
  onClose,
  onSaved,
}: {
  choices: Choice[]
  onClose: () => void
  onSaved: () => Promise<void>
}) {
  const [value, setValue] = useState(choices[0]?.value ?? '')
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const [kind, id] = value.split(':')
    try {
      if (kind === 'place') await knowledgeBaseApi.add({ place_id: id })
      else await knowledgeBaseApi.add({ partner_id: id })
      await onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось добавить в базу знаний')
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
        aria-label="Добавить в базу знаний"
        className="mt-8 w-full max-w-lg rounded-lg bg-white p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="mb-6 text-xl font-semibold tracking-tight">Добавить в базу знаний</h2>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          {error ? <p role="alert">{error}</p> : null}
          <label className="flex flex-col gap-1 text-sm">
            Бизнес
            <select
              value={value}
              onChange={(event) => setValue(event.target.value)}
              className="rounded border border-slate-300 bg-white px-3 py-2"
              required
            >
              {choices.map((choice) => (
                <option key={choice.value} value={choice.value}>
                  {choice.label}
                </option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            className="rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
          >
            Сохранить
          </button>
        </form>
      </div>
    </div>
  )
}
