import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { partnerTypesApi, type PartnerType } from '../partner-types/partnerTypesApi'
import { PartnerFormModal } from './PartnerFormModal'
import { partnersApi, type Partner } from './partnersApi'

export function PartnersPage() {
  const [partners, setPartners] = useState<Partner[]>([])
  const [types, setTypes] = useState<PartnerType[]>([])
  const [error, setError] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [modal, setModal] = useState<{ mode: 'create' | 'edit'; partnerId?: string } | null>(
    null,
  )
  const menuRef = useRef<HTMLDivElement>(null)

  async function reload() {
    const [partnerItems, typeItems] = await Promise.all([
      partnersApi.list(),
      partnerTypesApi.list(),
    ])
    setPartners(partnerItems)
    setTypes(typeItems)
  }

  useEffect(() => {
    let cancelled = false
    reload()
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!menuOpen) return
    function onPointerDown(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [menuOpen])

  const typeLabel = Object.fromEntries(types.map((t) => [t.slug, t.topic_label]))

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Партнёры</h1>
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
            aria-haspopup="menu"
            aria-expanded={menuOpen}
          >
            Управлять партнёрами
          </button>
          {menuOpen ? (
            <div
              role="menu"
              className="absolute right-0 z-10 mt-1 min-w-48 rounded border border-slate-200 bg-white py-1 shadow-md"
            >
              <button
                type="button"
                role="menuitem"
                className="block w-full px-3 py-2 text-left text-sm hover:bg-slate-50"
                onClick={() => {
                  setMenuOpen(false)
                  setModal({ mode: 'create' })
                }}
              >
                Добавить партнёра
              </button>
              <Link
                role="menuitem"
                to="/partner-types"
                className="block w-full px-3 py-2 text-left text-sm hover:bg-slate-50"
                onClick={() => setMenuOpen(false)}
              >
                Типы партнёров
              </Link>
            </div>
          ) : null}
        </div>
      </div>
      {error ? <p role="alert">{error}</p> : null}
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-slate-300">
            <th className="py-2 pr-4 font-medium">Имя</th>
            <th className="py-2 pr-4 font-medium">Тип</th>
            <th className="py-2 pr-4 font-medium">Порядок</th>
            <th className="py-2 pr-4 font-medium">Активен</th>
            <th className="py-2 font-medium">Действия</th>
          </tr>
        </thead>
        <tbody>
          {partners.map((partner) => (
            <tr key={partner.id} className="border-b border-slate-200">
              <td className="py-2 pr-4">{partner.name}</td>
              <td className="py-2 pr-4">{typeLabel[partner.type] ?? 'Без названия'}</td>
              <td className="py-2 pr-4">{partner.sort_order}</td>
              <td className="py-2 pr-4">{partner.is_active ? 'да' : 'нет'}</td>
              <td className="py-2">
                <button
                  type="button"
                  className="text-slate-700 underline hover:text-slate-900"
                  onClick={() => setModal({ mode: 'edit', partnerId: partner.id })}
                >
                  Изменить
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {modal ? (
        <PartnerFormModal
          mode={modal.mode}
          partnerId={modal.partnerId}
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
