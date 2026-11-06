import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { PartnerTypeFormModal } from '../partner-types/PartnerTypeFormModal'
import { partnerTypesApi, type PartnerType } from '../partner-types/partnerTypesApi'
import { Icon } from '../shell/icons'
import { PartnerFormModal } from './PartnerFormModal'
import { partnersApi, type Partner } from './partnersApi'

const PAGE_SIZE = 8

function countLabel(count: number): string {
  const n = Math.abs(count) % 100
  const n1 = n % 10
  const word =
    n > 10 && n < 20 ? 'партнёров' : n1 === 1 ? 'партнёр' : n1 > 1 && n1 < 5 ? 'партнёра' : 'партнёров'
  return `${count} ${word}`
}

function RowMenu({ label, onEdit }: { label: string; onEdit: () => void }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const popRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const itemRef = useRef<HTMLButtonElement>(null)
  const [pos, setPos] = useState({ top: 0, left: 0 })

  useEffect(() => {
    if (!open) return
    function place() {
      const rect = buttonRef.current?.getBoundingClientRect()
      if (!rect) return
      setPos({ top: rect.bottom + 6, left: rect.right })
    }
    place()
    function onPointer(event: MouseEvent) {
      const target = event.target as Node
      if (rootRef.current?.contains(target) || popRef.current?.contains(target)) return
      setOpen(false)
    }
    function onKey(event: KeyboardEvent) {
      if (event.key !== 'Escape') return
      setOpen(false)
      buttonRef.current?.focus()
    }
    window.addEventListener('resize', place)
    window.addEventListener('scroll', place, true)
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    itemRef.current?.focus()
    return () => {
      window.removeEventListener('resize', place)
      window.removeEventListener('scroll', place, true)
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div className="row-menu" ref={rootRef}>
      <button
        ref={buttonRef}
        type="button"
        className="icon-button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Действия: ${label}`}
        onClick={() => setOpen((value) => !value)}
      >
        <Icon name="dots" />
      </button>
      {open
        ? createPortal(
            <div
              ref={popRef}
              role="menu"
              className="row-menu-pop"
              style={{ top: pos.top, left: pos.left }}
            >
              <button
                ref={itemRef}
                type="button"
                role="menuitem"
                onClick={() => {
                  setOpen(false)
                  onEdit()
                }}
              >
                Изменить
              </button>
            </div>,
            document.body,
          )
        : null}
    </div>
  )
}

export function PartnersPage() {
  const [partners, setPartners] = useState<Partner[] | null>(null)
  const [types, setTypes] = useState<PartnerType[] | null>(null)
  const [partnerError, setPartnerError] = useState<string | null>(null)
  const [typeError, setTypeError] = useState<string | null>(null)
  const [pageIndex, setPageIndex] = useState(0)
  const [partnerModal, setPartnerModal] = useState<{ mode: 'create' | 'edit'; partnerId?: string } | null>(
    null,
  )
  const [typeModal, setTypeModal] = useState<{ mode: 'create' | 'edit'; slug?: string } | null>(null)

  async function reloadPartners() {
    setPartners(await partnersApi.list())
  }

  async function reloadTypes() {
    setTypes(await partnerTypesApi.list())
  }

  useEffect(() => {
    let cancelled = false
    reloadPartners().catch((err: Error) => {
      if (!cancelled) setPartnerError(err.message)
    })
    reloadTypes().catch((err: Error) => {
      if (!cancelled) setTypeError(err.message)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const typeLabel = Object.fromEntries((types ?? []).map((type) => [type.slug, type.topic_label]))
  const list = partners ?? []
  const pageCount = Math.max(1, Math.ceil(list.length / PAGE_SIZE))
  const page = Math.min(pageIndex, pageCount - 1)
  const pageRows = list.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE)

  return (
    <main className="roster">
      <div className="roster-head">
        <div>
          <h1>Партнёры</h1>
          <p>Управляйте партнёрами и их данными</p>
        </div>
        <button type="button" className="ice-button roster-add" onClick={() => setPartnerModal({ mode: 'create' })}>
          <Icon name="plus" size={16} />
          Добавить партнёра
        </button>
      </div>

      <div className="roster-split">
        <section className="glass-pane roster-card" aria-label="Список партнёров">
          {partnerError ? <p role="alert">{partnerError}</p> : null}
          {partners === null ? (
            partnerError ? null : (
              <p className="roster-status">Загрузка…</p>
            )
          ) : (
            <>
              <div className="roster-scroll">
                <table className="roster-table">
                  <thead>
                    <tr>
                      <th>Лого</th>
                      <th>Имя</th>
                      <th>Тип</th>
                      <th>Порядок</th>
                      <th>Активен</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pageRows.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="roster-empty">
                          Партнёров пока нет. Добавьте первого кнопкой выше.
                        </td>
                      </tr>
                    ) : (
                      pageRows.map((partner) => (
                        <tr key={partner.id}>
                          <td>
                            {partner.logo_url ? (
                              <img
                                src={partner.logo_url}
                                alt={`Логотип ${partner.name}`}
                                className="roster-logo"
                              />
                            ) : (
                              <span className="roster-logo-fallback" aria-hidden="true">
                                {Array.from(partner.name)[0] ?? ''}
                              </span>
                            )}
                          </td>
                          <td className="roster-name">{partner.name}</td>
                          <td>{typeLabel[partner.type] ?? 'Без названия'}</td>
                          <td className="roster-num">{partner.sort_order}</td>
                          <td>
                            <span className={partner.is_active ? 'status-pill is-on' : 'status-pill is-off'}>
                              {partner.is_active ? 'Да' : 'Нет'}
                            </span>
                          </td>
                          <td className="roster-actions">
                            <RowMenu
                              label={partner.name}
                              onEdit={() => setPartnerModal({ mode: 'edit', partnerId: partner.id })}
                            />
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              <div className="roster-foot">
                <p>{countLabel(list.length)}</p>
                <div className="roster-pager">
                  <button
                    type="button"
                    className="icon-button"
                    aria-label="Предыдущая страница"
                    disabled={page === 0}
                    onClick={() => setPageIndex(page - 1)}
                  >
                    <Icon name="chevronLeft" />
                  </button>
                  <button
                    type="button"
                    className="icon-button"
                    aria-label="Следующая страница"
                    disabled={page >= pageCount - 1}
                    onClick={() => setPageIndex(page + 1)}
                  >
                    <Icon name="chevronRight" />
                  </button>
                </div>
              </div>
            </>
          )}
        </section>

        <aside className="glass-pane roster-types" aria-label="Типы партнёров">
          <div className="type-head">
            <h2>Типы партнёров</h2>
            <button type="button" className="ghost-button" onClick={() => setTypeModal({ mode: 'create' })}>
              Добавить тип
            </button>
          </div>
          {typeError ? <p role="alert">{typeError}</p> : null}
          {types === null ? (
            typeError ? null : (
              <p className="roster-status">Загрузка…</p>
            )
          ) : types.length === 0 ? (
            <p className="roster-empty">Типов пока нет. Добавьте тип, чтобы назначать его партнёрам.</p>
          ) : (
            <ul className="type-list">
              {types.map((type) => (
                <li key={type.slug} className="type-row">
                  <span>{type.topic_label}</span>
                  <span className={type.is_menu_visible ? 'status-pill is-on' : 'status-pill is-off'}>
                    {type.is_menu_visible ? 'В меню' : 'Скрыт'}
                  </span>
                  <RowMenu
                    label={type.topic_label}
                    onEdit={() => setTypeModal({ mode: 'edit', slug: type.slug })}
                  />
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>

      {partnerModal ? (
        <PartnerFormModal
          mode={partnerModal.mode}
          partnerId={partnerModal.partnerId}
          types={types ?? []}
          onClose={() => setPartnerModal(null)}
          onChanged={() => {
            void partnersApi.list().then(setPartners).catch((err: Error) => setPartnerError(err.message))
          }}
          onSaved={async () => {
            const created = partnerModal.mode === 'create'
            setPartnerModal(null)
            const next = await partnersApi.list()
            setPartners(next)
            if (created) setPageIndex(Math.max(0, Math.ceil(next.length / PAGE_SIZE) - 1))
          }}
        />
      ) : null}

      {typeModal ? (
        <PartnerTypeFormModal
          mode={typeModal.mode}
          slug={typeModal.slug}
          onClose={() => setTypeModal(null)}
          onSaved={async () => {
            setTypeModal(null)
            await reloadTypes()
          }}
        />
      ) : null}
    </main>
  )
}
