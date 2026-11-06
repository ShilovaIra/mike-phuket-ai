import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { partnerTypesApi, type PartnerType } from '../partner-types/partnerTypesApi'
import { partnersApi, type Partner } from '../partners/partnersApi'
import { placeCategoriesApi, type PlaceCategory } from '../place-categories/placeCategoriesApi'
import { placesApi, type Place } from '../places/placesApi'
import { Icon } from '../shell/icons'
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

function entryMark(
  entry: KnowledgeBaseEntry,
  partners: Partner[],
  places: Place[],
): { src: string | null; alt: string; letter: string } {
  const letter = Array.from(entry.name.trim())[0] ?? '?'
  if (entry.partner_id) {
    const partner = partners.find((item) => item.id === entry.partner_id)
    if (partner?.logo_url) return { src: partner.logo_url, alt: `Логотип ${partner.name}`, letter }
    return { src: null, alt: letter, letter }
  }
  const place = places.find((item) => item.id === entry.place_id)
  const photo = place?.photos.find((item) => item.url)?.url
  if (photo) return { src: photo, alt: `Фото ${entry.name}`, letter }
  if (place?.partner_id) {
    const partner = partners.find((item) => item.id === place.partner_id)
    if (partner?.logo_url) return { src: partner.logo_url, alt: `Логотип ${partner.name}`, letter }
  }
  return { src: null, alt: letter, letter }
}

function matchesQuery(entry: KnowledgeBaseEntry, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return [entry.name, entry.referral_url, entry.maps_url].some((value) =>
    value.toLowerCase().includes(needle),
  )
}

function LinkLine({ href }: { href: string }) {
  if (!href) return null
  return (
    <a className="roster-link" href={href} target="_blank" rel="noreferrer" title={href}>
      <Icon name="link" size={14} />
      <span>{href}</span>
    </a>
  )
}

export function KnowledgeBasePage() {
  const [entries, setEntries] = useState<KnowledgeBaseEntry[] | null>(null)
  const [partners, setPartners] = useState<Partner[]>([])
  const [places, setPlaces] = useState<Place[]>([])
  const [choices, setChoices] = useState<Choice[]>([])
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [kind, setKind] = useState('')
  const [adding, setAdding] = useState(false)

  async function reload() {
    const [nextEntries, nextPartners, types, nextPlaces, categories] = await Promise.all([
      knowledgeBaseApi.list(),
      partnersApi.list(),
      partnerTypesApi.list(),
      placesApi.list(),
      placeCategoriesApi.list(),
    ])
    setEntries(nextEntries)
    setPartners(nextPartners)
    setPlaces(nextPlaces)
    setChoices(addableChoices(nextEntries, nextPartners, types, nextPlaces, categories))
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

  const kinds = useMemo(() => {
    const labels = new Set((entries ?? []).map((entry) => entry.kind).filter(Boolean))
    return [...labels].sort((a, b) => a.localeCompare(b, 'ru'))
  }, [entries])

  useEffect(() => {
    if (kind && !kinds.includes(kind)) setKind('')
  }, [kind, kinds])

  const visible = (entries ?? []).filter((entry) => {
    if (kind && entry.kind !== kind) return false
    return matchesQuery(entry, query)
  })

  return (
    <main className="roster">
      <div className="roster-head">
        <div>
          <h1>База знаний</h1>
          <p>Справочная информация: партнёры, ссылки и полезные ресурсы</p>
        </div>
        <button
          type="button"
          className="ice-button roster-add"
          disabled={entries === null}
          onClick={() => setAdding(true)}
        >
          <Icon name="plus" size={16} />
          Добавить запись
        </button>
      </div>

      <section className="glass-pane roster-card" aria-label="Список базы знаний">
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
        <div className="roster-tools">
          <label className="roster-search">
            <Icon name="search" size={16} />
            <input
              className="glass-field"
              type="search"
              value={query}
              placeholder="Поиск по названию или ссылке…"
              aria-label="Поиск по названию или ссылке"
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <label className="roster-filter">
            <select
              className="glass-field"
              aria-label="Вид"
              value={kind}
              onChange={(event) => setKind(event.target.value)}
            >
              <option value="">Все виды</option>
              {kinds.map((label) => (
                <option key={label} value={label}>
                  {label}
                </option>
              ))}
            </select>
            <Icon name="chevronDown" size={16} />
          </label>
        </div>

        {entries === null ? (
          error ? null : (
            <p className="roster-status">Загрузка…</p>
          )
        ) : (
          <div className="roster-scroll">
            <table className="roster-table">
              <thead>
                <tr>
                  <th scope="col">Название</th>
                  <th scope="col">Вид</th>
                  <th scope="col">Ссылка</th>
                  <th scope="col">В чате</th>
                  <th scope="col">Действия</th>
                </tr>
              </thead>
              <tbody>
                {visible.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="roster-empty">
                      {entries.length === 0
                        ? 'Записей пока нет. Добавьте партнёра или место кнопкой выше.'
                        : 'Ничего не найдено. Измените поиск или фильтр.'}
                    </td>
                  </tr>
                ) : (
                  visible.map((entry) => {
                    const mark = entryMark(entry, partners, places)
                    return (
                      <tr key={entry.id}>
                        <td>
                          <div className="roster-identity">
                            {mark.src ? (
                              <img src={mark.src} alt={mark.alt} className="roster-logo" />
                            ) : (
                              <span className="roster-logo-fallback" aria-hidden="true">
                                {mark.letter}
                              </span>
                            )}
                            <span className="roster-name">{entry.name}</span>
                          </div>
                        </td>
                        <td>
                          <span className="kind-pill">{entry.kind || '—'}</span>
                        </td>
                        <td>
                          <div className="roster-links">
                            <LinkLine href={entry.referral_url} />
                            <LinkLine href={entry.maps_url} />
                            {!entry.referral_url && !entry.maps_url ? '—' : null}
                          </div>
                        </td>
                        <td>
                          <span className={entry.in_chat ? 'status-pill is-on' : 'status-pill is-off'}>
                            {entry.in_chat ? 'Да' : 'Нет'}
                          </span>
                        </td>
                        <td className="roster-actions is-pair">
                          <button
                            type="button"
                            className="icon-button is-danger"
                            aria-label={`Удалить: ${entry.name}`}
                            onClick={async () => {
                              try {
                                await knowledgeBaseApi.remove(entry.id)
                                await reload()
                              } catch (err) {
                                setError(
                                  err instanceof Error ? err.message : 'Не удалось удалить из базы знаний',
                                )
                              }
                            }}
                          >
                            <Icon name="trash" size={16} />
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

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
  const [pending, setPending] = useState(false)

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (pending || !value) return
    const [kind, id] = value.split(':')
    setPending(true)
    try {
      if (kind === 'place') await knowledgeBaseApi.add({ place_id: id })
      else await knowledgeBaseApi.add({ partner_id: id })
      await onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось добавить в базу знаний')
      setPending(false)
    }
  }

  return (
    <div className="roster-modal" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="knowledge-add-title"
        className="glass-pane roster-dialog"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="knowledge-add-title">Добавить в базу знаний</h2>
        <form onSubmit={onSubmit} className="roster-form">
          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
          {choices.length === 0 ? (
            <p>Нечего добавить. Все партнёры и места уже в базе.</p>
          ) : (
            <label>
              Бизнес
              <select
                value={value}
                onChange={(event) => setValue(event.target.value)}
                className="glass-field"
                required
              >
                {choices.map((choice) => (
                  <option key={choice.value} value={choice.value}>
                    {choice.label}
                  </option>
                ))}
              </select>
            </label>
          )}
          <div className="roster-form-actions">
            <button type="submit" className="ice-button" disabled={pending || choices.length === 0}>
              Сохранить
            </button>
            <button type="button" className="ghost-button" onClick={onClose}>
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
