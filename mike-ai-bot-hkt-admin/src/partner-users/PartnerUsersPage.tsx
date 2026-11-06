import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { formatBangkok } from '../broadcasts/formatBangkok'
import { partnersApi, type Partner } from '../partners/partnersApi'
import { Icon } from '../shell/icons'
import { partnerUsersApi, type PartnerUserRow } from './partnerUsersApi'

function matchesQuery(row: PartnerUserRow, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  if (row.email.toLowerCase().includes(needle)) return true
  return row.partners.some((partner) => partner.name.toLowerCase().includes(needle))
}

function userMark(row: PartnerUserRow, partners: Partner[]): { src: string | null; alt: string } {
  const letter = (Array.from(row.email.trim())[0] ?? '?').toUpperCase()
  if (row.partners.length !== 1) return { src: null, alt: letter }
  const partner = partners.find((item) => item.id === row.partners[0]?.id)
  if (!partner?.logo_url) return { src: null, alt: letter }
  return { src: partner.logo_url, alt: `Логотип ${partner.name}` }
}

export function PartnerUsersPage() {
  const [users, setUsers] = useState<PartnerUserRow[] | null>(null)
  const [partners, setPartners] = useState<Partner[]>([])
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [partnerId, setPartnerId] = useState('')
  const [modal, setModal] = useState<{ mode: 'create' } | { mode: 'edit'; user: PartnerUserRow } | null>(
    null,
  )

  async function reload() {
    const [userItems, partnerItems] = await Promise.all([partnerUsersApi.list(), partnersApi.list()])
    setUsers(userItems)
    setPartners(partnerItems)
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

  const partnerOptions = useMemo(
    () => [...partners].sort((a, b) => a.name.localeCompare(b.name, 'ru')),
    [partners],
  )

  const visible = (users ?? []).filter((row) => {
    if (partnerId && !row.partners.some((partner) => partner.id === partnerId)) return false
    return matchesQuery(row, query)
  })

  return (
    <main className="roster">
      <div className="roster-head">
        <div>
          <h1>Пользователи партнёров</h1>
          <p>Управляйте доступом партнёров к системе</p>
        </div>
        <button
          type="button"
          className="ice-button roster-add"
          disabled={users === null}
          onClick={() => setModal({ mode: 'create' })}
        >
          <Icon name="plus" size={16} />
          Добавить пользователя
        </button>
      </div>

      <section className="glass-pane roster-card" aria-label="Список пользователей партнёров">
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
              placeholder="Поиск по email или партнёру…"
              aria-label="Поиск по email или партнёру"
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <label className="roster-filter">
            <select
              className="glass-field"
              aria-label="Партнёр"
              value={partnerId}
              onChange={(event) => setPartnerId(event.target.value)}
            >
              <option value="">Все партнёры</option>
              {partnerOptions.map((partner) => (
                <option key={partner.id} value={partner.id}>
                  {partner.name}
                </option>
              ))}
            </select>
            <Icon name="chevronDown" size={16} />
          </label>
        </div>

        {users === null ? (
          error ? null : (
            <p className="roster-status">Загрузка…</p>
          )
        ) : (
          <div className="roster-scroll">
            <table className="roster-table">
              <thead>
                <tr>
                  <th scope="col">Email</th>
                  <th scope="col">Партнёр</th>
                  <th scope="col">Дата добавления</th>
                  <th scope="col">Действия</th>
                </tr>
              </thead>
              <tbody>
                {visible.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="roster-empty">
                      {users.length === 0
                        ? 'Пользователей пока нет. Добавьте первого кнопкой выше.'
                        : 'Никого не найдено. Измените поиск или фильтр.'}
                    </td>
                  </tr>
                ) : (
                  visible.map((row) => {
                    const mark = userMark(row, partners)
                    return (
                      <tr key={row.id}>
                        <td>
                          <div className="roster-identity">
                            {mark.src ? (
                              <img src={mark.src} alt={mark.alt} className="roster-logo" />
                            ) : (
                              <span className="roster-logo-fallback" aria-hidden="true">
                                {mark.alt}
                              </span>
                            )}
                            <span className="roster-name">{row.email}</span>
                          </div>
                        </td>
                        <td className="roster-partners">
                          {row.partners.length > 0
                            ? row.partners.map((partner) => partner.name).join(', ')
                            : '—'}
                        </td>
                        <td className="roster-num">
                          <time dateTime={row.created_at}>{formatBangkok(row.created_at)}</time>
                        </td>
                        <td className="roster-actions is-pair">
                          <button
                            type="button"
                            className="icon-button"
                            aria-label={`Изменить: ${row.email}`}
                            onClick={() => setModal({ mode: 'edit', user: row })}
                          >
                            <Icon name="pencil" size={16} />
                          </button>
                          <button
                            type="button"
                            className="icon-button is-danger"
                            aria-label={`Удалить: ${row.email}`}
                            onClick={async () => {
                              try {
                                await partnerUsersApi.remove(row.id)
                                await reload()
                              } catch (err) {
                                setError(err instanceof Error ? err.message : 'Не удалось удалить пользователя')
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

      {modal ? (
        <PartnerUserModal
          mode={modal.mode}
          user={modal.mode === 'edit' ? modal.user : undefined}
          partners={partnerOptions}
          onClose={() => setModal(null)}
          onSaved={async () => {
            setModal(null)
            await reload()
          }}
        />
      ) : null}
    </main>
  )
}

function PartnerUserModal({
  mode,
  user,
  partners,
  onClose,
  onSaved,
}: {
  mode: 'create' | 'edit'
  user?: PartnerUserRow
  partners: Partner[]
  onClose: () => void
  onSaved: () => Promise<void>
}) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [selected, setSelected] = useState<string[]>(() => user?.partners.map((partner) => partner.id) ?? [])
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
    if (pending) return
    if (selected.length === 0) {
      setError('Выберите хотя бы одного партнёра')
      return
    }
    setPending(true)
    try {
      if (mode === 'create') {
        await partnerUsersApi.create({ email, password, partner_ids: selected })
      } else if (user) {
        await partnerUsersApi.update(user.id, {
          partner_ids: selected,
          ...(password ? { password } : {}),
        })
      }
      await onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить')
      setPending(false)
    }
  }

  const title = mode === 'create' ? 'Новый пользователь' : 'Изменить пользователя'

  return (
    <div className="roster-modal" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="partner-user-title"
        className="glass-pane roster-dialog"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="partner-user-title">{title}</h2>
        <form onSubmit={onSubmit} className="roster-form">
          {mode === 'create' ? (
            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="glass-field"
                required
                autoComplete="off"
              />
            </label>
          ) : (
            <p className="roster-locked">{user?.email}</p>
          )}
          <label>
            {mode === 'create' ? 'Пароль' : 'Новый пароль'}
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="glass-field"
              required={mode === 'create'}
              autoComplete="new-password"
              placeholder={mode === 'edit' ? 'Оставьте пустым, чтобы не менять' : undefined}
            />
          </label>
          <fieldset className="roster-checks">
            <legend>Партнёры</legend>
            {partners.length === 0 ? (
              <p>Нет партнёров. Сначала добавьте их в разделе «Партнёры».</p>
            ) : (
              partners.map((partner) => (
                <label key={partner.id}>
                  <input
                    type="checkbox"
                    checked={selected.includes(partner.id)}
                    onChange={(event) => {
                      setSelected((prev) =>
                        event.target.checked
                          ? [...prev, partner.id]
                          : prev.filter((id) => id !== partner.id),
                      )
                    }}
                  />
                  {partner.name}
                </label>
              ))
            )}
          </fieldset>
          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
          <div className="roster-form-actions">
            <button type="submit" className="ice-button" disabled={pending}>
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
