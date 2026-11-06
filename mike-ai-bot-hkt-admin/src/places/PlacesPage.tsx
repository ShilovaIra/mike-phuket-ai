import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { PlaceCategoryFormModal } from '../place-categories/PlaceCategoryFormModal'
import { placeCategoriesApi, type PlaceCategory } from '../place-categories/placeCategoriesApi'
import placeholder from '../assets/placeholders/empty_picture_placeholder.jpg'
import { Icon } from '../shell/icons'
import { PlaceFormModal } from './PlaceFormModal'
import { placesApi, type Place } from './placesApi'

const PAGE_SIZE = 8

function placeMatches(place: Place, query: string, label: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return [place.name, place.blurb, label].some((value) => value.toLowerCase().includes(needle))
}

function categoryMatches(category: PlaceCategory, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return [category.slug, category.label].some((value) => value.toLowerCase().includes(needle))
}

function Flag({ on }: { on: boolean }) {
  return (
    <span className={on ? 'status-pill is-on has-mark' : 'status-pill is-quiet has-mark'}>
      {on ? <Icon name="check" size={14} /> : <span className="status-mark" aria-hidden="true" />}
      {on ? 'Да' : 'Нет'}
    </span>
  )
}

function Pager({
  page,
  pageCount,
  onPage,
}: {
  page: number
  pageCount: number
  onPage: (page: number) => void
}) {
  return (
    <div className="roster-pager">
      <button
        type="button"
        className="icon-button"
        aria-label="Предыдущая страница"
        disabled={page === 0}
        onClick={() => onPage(page - 1)}
      >
        <Icon name="chevronLeft" />
      </button>
      <span className="roster-page" aria-current="page">
        {page + 1}
      </span>
      <button
        type="button"
        className="icon-button"
        aria-label="Следующая страница"
        disabled={page >= pageCount - 1}
        onClick={() => onPage(page + 1)}
      >
        <Icon name="chevronRight" />
      </button>
    </div>
  )
}

export function PlacesPage() {
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') === 'categories' ? 'categories' : 'places'
  const [places, setPlaces] = useState<Place[] | null>(null)
  const [categories, setCategories] = useState<PlaceCategory[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [placeQuery, setPlaceQuery] = useState('')
  const [categoryQuery, setCategoryQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [placePage, setPlacePage] = useState(0)
  const [categoryPage, setCategoryPage] = useState(0)
  const [creatingPlace, setCreatingPlace] = useState(false)
  const [editingPlace, setEditingPlace] = useState<Place | null>(null)
  const [creatingCategory, setCreatingCategory] = useState(false)
  const [editingCategory, setEditingCategory] = useState<PlaceCategory | null>(null)

  async function reload() {
    const [loadedPlaces, loadedCategories] = await Promise.all([
      placesApi.list(),
      placeCategoriesApi.list(),
    ])
    setPlaces(loadedPlaces)
    setCategories(loadedCategories)
    return { places: loadedPlaces, categories: loadedCategories }
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

  useEffect(() => {
    if (categoryFilter && categories && !categories.some((category) => category.slug === categoryFilter)) {
      setCategoryFilter('')
    }
  }, [categories, categoryFilter])

  const labelFor = (slug: string) => categories?.find((category) => category.slug === slug)?.label ?? slug
  const usedSlugs = new Set((places ?? []).map((place) => place.category))

  const filteredPlaces = (places ?? [])
    .filter((place) => (categoryFilter ? place.category === categoryFilter : true))
    .filter((place) => {
      if (statusFilter === 'active') return place.is_active
      if (statusFilter === 'inactive') return !place.is_active
      return true
    })
    .filter((place) => placeMatches(place, placeQuery, labelFor(place.category)))

  const filteredCategories = (categories ?? []).filter((category) =>
    categoryMatches(category, categoryQuery),
  )

  const placePageCount = Math.max(1, Math.ceil(filteredPlaces.length / PAGE_SIZE))
  const safePlacePage = Math.min(placePage, placePageCount - 1)
  const placeRows = filteredPlaces.slice(safePlacePage * PAGE_SIZE, safePlacePage * PAGE_SIZE + PAGE_SIZE)

  const categoryPageCount = Math.max(1, Math.ceil(filteredCategories.length / PAGE_SIZE))
  const safeCategoryPage = Math.min(categoryPage, categoryPageCount - 1)
  const categoryRows = filteredCategories.slice(
    safeCategoryPage * PAGE_SIZE,
    safeCategoryPage * PAGE_SIZE + PAGE_SIZE,
  )

  function openTab(next: 'places' | 'categories') {
    setParams(next === 'categories' ? { tab: 'categories' } : {}, { replace: false })
  }

  async function removeCategory(slug: string) {
    try {
      await placeCategoriesApi.remove(slug)
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить категорию')
    }
  }

  const loaded = places !== null && categories !== null

  return (
    <main className="roster">
      <div className="roster-head">
        <div>
          <h1>Места</h1>
          <p>Управляйте местами и категориями, которые отображаются в системе</p>
        </div>
        {tab === 'places' ? (
          <button
            type="button"
            className="ice-button roster-add"
            onClick={() => setCreatingPlace(true)}
          >
            <Icon name="plus" size={16} />
            Добавить место
          </button>
        ) : (
          <button
            type="button"
            className="ice-button roster-add"
            onClick={() => setCreatingCategory(true)}
          >
            <Icon name="plus" size={16} />
            Добавить категорию
          </button>
        )}
      </div>

      <div className="place-switch" role="tablist" aria-label="Раздел мест">
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'places'}
          className={`place-tab${tab === 'places' ? ' is-active' : ''}`}
          onClick={() => openTab('places')}
        >
          <Icon name="pin" size={16} />
          Места
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'categories'}
          className={`place-tab${tab === 'categories' ? ' is-active' : ''}`}
          onClick={() => openTab('categories')}
        >
          <Icon name="layers" size={16} />
          Категории
        </button>
      </div>

      <section className="glass-pane roster-card" aria-label={tab === 'places' ? 'Список мест' : 'Список категорий'}>
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}

        {tab === 'places' ? (
          <div className="roster-tools">
            <label className="roster-search">
              <Icon name="search" size={16} />
              <input
                className="glass-field"
                type="search"
                value={placeQuery}
                placeholder="Поиск по названию, описанию или категории…"
                aria-label="Поиск по названию, описанию или категории"
                onChange={(event) => {
                  setPlaceQuery(event.target.value)
                  setPlacePage(0)
                }}
              />
            </label>
            <label className="roster-filter">
              <select
                className="glass-field"
                aria-label="Категория"
                value={categoryFilter}
                onChange={(event) => {
                  setCategoryFilter(event.target.value)
                  setPlacePage(0)
                }}
              >
                <option value="">Все категории</option>
                {(categories ?? []).map((category) => (
                  <option key={category.slug} value={category.slug}>
                    {category.label}
                  </option>
                ))}
              </select>
              <Icon name="chevronDown" size={16} />
            </label>
            <label className="roster-filter">
              <select
                className="glass-field"
                aria-label="Статус"
                value={statusFilter}
                onChange={(event) => {
                  setStatusFilter(event.target.value)
                  setPlacePage(0)
                }}
              >
                <option value="">Все статусы</option>
                <option value="active">Активные</option>
                <option value="inactive">Неактивные</option>
              </select>
              <Icon name="chevronDown" size={16} />
            </label>
          </div>
        ) : (
          <div className="roster-tools">
            <label className="roster-search">
              <Icon name="search" size={16} />
              <input
                className="glass-field"
                type="search"
                value={categoryQuery}
                placeholder="Поиск по названию или slug…"
                aria-label="Поиск по названию или slug"
                onChange={(event) => {
                  setCategoryQuery(event.target.value)
                  setCategoryPage(0)
                }}
              />
            </label>
          </div>
        )}

        {!loaded ? (
          error ? null : (
            <p className="roster-status">Загрузка…</p>
          )
        ) : tab === 'places' ? (
          <>
            <div className="roster-scroll">
              <table className="roster-table place-table">
                <thead>
                  <tr>
                    <th scope="col">Фото</th>
                    <th scope="col">Название</th>
                    <th scope="col">Категория</th>
                    <th scope="col">Описание</th>
                    <th scope="col">Активно</th>
                    <th scope="col">Рекомендует</th>
                    <th scope="col">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {placeRows.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="roster-empty">
                        {places.length === 0
                          ? 'Мест пока нет. Добавьте первое кнопкой выше.'
                          : 'Ничего не найдено. Измените поиск или фильтр.'}
                      </td>
                    </tr>
                  ) : (
                    placeRows.map((place) => (
                      <tr key={place.id}>
                        <td>
                          <img
                            src={place.photos[0]?.url || placeholder}
                            alt={`Фото ${place.name}`}
                            className="place-thumb"
                          />
                        </td>
                        <td className="roster-name">{place.name}</td>
                        <td>
                          <span className="place-chip">
                            <Icon name="pin" size={14} />
                            {labelFor(place.category)}
                          </span>
                        </td>
                        <td>
                          {place.blurb ? (
                            <span className="place-blurb">{place.blurb}</span>
                          ) : (
                            <span className="place-blurb">—</span>
                          )}
                        </td>
                        <td>
                          <Flag on={place.is_active} />
                        </td>
                        <td>
                          <Flag on={place.mike_recommends} />
                        </td>
                        <td className="roster-actions">
                          <button
                            type="button"
                            className="icon-button"
                            aria-label={`Изменить: ${place.name}`}
                            onClick={() => setEditingPlace(place)}
                          >
                            <Icon name="pencil" size={16} />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className="roster-foot">
              <p>
                Показано {placeRows.length} из {filteredPlaces.length}
              </p>
              <Pager page={safePlacePage} pageCount={placePageCount} onPage={setPlacePage} />
            </div>
          </>
        ) : (
          <>
            <div className="roster-scroll">
              <table className="roster-table">
                <thead>
                  <tr>
                    <th scope="col">Slug</th>
                    <th scope="col">Название</th>
                    <th scope="col">Порядок</th>
                    <th scope="col">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {categoryRows.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="roster-empty">
                        {categories.length === 0
                          ? 'Категорий пока нет. Добавьте категорию кнопкой выше.'
                          : 'Ничего не найдено. Измените поиск.'}
                      </td>
                    </tr>
                  ) : (
                    categoryRows.map((category) => (
                      <tr key={category.slug}>
                        <td>{category.slug}</td>
                        <td className="roster-name">{category.label}</td>
                        <td className="roster-num">{category.sort_order}</td>
                        <td className="roster-actions is-pair">
                          <button
                            type="button"
                            className="icon-button"
                            aria-label={`Изменить: ${category.label}`}
                            onClick={() => setEditingCategory(category)}
                          >
                            <Icon name="pencil" size={16} />
                          </button>
                          {usedSlugs.has(category.slug) ? null : (
                            <button
                              type="button"
                              className="icon-button is-danger"
                              aria-label={`Удалить: ${category.label}`}
                              onClick={() => void removeCategory(category.slug)}
                            >
                              <Icon name="trash" size={16} />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className="roster-foot">
              <p>
                Показано {categoryRows.length} из {filteredCategories.length}
              </p>
              <Pager page={safeCategoryPage} pageCount={categoryPageCount} onPage={setCategoryPage} />
            </div>
          </>
        )}
      </section>

      {creatingPlace ? (
        <PlaceFormModal
          onClose={() => setCreatingPlace(false)}
          onChanged={async () => {
            await reload()
          }}
          onSaved={() => {
            setCreatingPlace(false)
            setPlaceQuery('')
            setCategoryFilter('')
            setStatusFilter('')
            void reload().then((next) => {
              setPlacePage(Math.max(0, Math.ceil(next.places.length / PAGE_SIZE) - 1))
            })
          }}
        />
      ) : null}
      {editingPlace ? (
        <PlaceFormModal
          place={editingPlace}
          onClose={() => setEditingPlace(null)}
          onChanged={async () => {
            await reload()
          }}
          onSaved={() => {
            setEditingPlace(null)
            void reload()
          }}
        />
      ) : null}
      {creatingCategory ? (
        <PlaceCategoryFormModal
          onClose={() => setCreatingCategory(false)}
          onSaved={() => {
            setCreatingCategory(false)
            setCategoryQuery('')
            void reload().then((next) => {
              setCategoryPage(Math.max(0, Math.ceil(next.categories.length / PAGE_SIZE) - 1))
            })
          }}
        />
      ) : null}
      {editingCategory ? (
        <PlaceCategoryFormModal
          category={editingCategory}
          onClose={() => setEditingCategory(null)}
          onSaved={() => {
            setEditingCategory(null)
            void reload()
          }}
        />
      ) : null}
    </main>
  )
}
