import { useEffect, useState } from 'react'
import { partnerTypesApi, type PartnerType } from '../partner-types/partnerTypesApi'
import { PartnerFormModal } from './PartnerFormModal'
import { partnersApi, type Partner } from './partnersApi'

export function PartnersPage() {
  const [partners, setPartners] = useState<Partner[]>([])
  const [types, setTypes] = useState<PartnerType[]>([])
  const [error, setError] = useState<string | null>(null)
  const [modal, setModal] = useState<{ mode: 'create' | 'edit'; partnerId?: string } | null>(
    null,
  )

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
    reload().catch((err: Error) => {
      if (!cancelled) setError(err.message)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const typeLabel = Object.fromEntries(types.map((t) => [t.slug, t.topic_label]))

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Партнёры</h1>
        <button
          type="button"
          onClick={() => setModal({ mode: 'create' })}
          className="rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
        >
          Добавить партнёра
        </button>
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
