import { useEffect, useState } from 'react'
import { PartnerTypeFormModal } from './PartnerTypeFormModal'
import { partnerTypesApi, type PartnerType } from './partnerTypesApi'

export function PartnerTypesPage() {
  const [types, setTypes] = useState<PartnerType[]>([])
  const [error, setError] = useState<string | null>(null)
  const [modal, setModal] = useState<{ mode: 'create' | 'edit'; slug?: string } | null>(null)

  async function reload() {
    setTypes(await partnerTypesApi.list())
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
        <h1 className="text-2xl font-semibold tracking-tight">Типы партнёров</h1>
        <button
          type="button"
          onClick={() => setModal({ mode: 'create' })}
          className="rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
        >
          Добавить тип
        </button>
      </div>
      {error ? <p role="alert">{error}</p> : null}
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-slate-300">
            <th className="py-2 pr-4 font-medium">Slug</th>
            <th className="py-2 pr-4 font-medium">Тема</th>
            <th className="py-2 pr-4 font-medium">Порядок</th>
            <th className="py-2 pr-4 font-medium">В меню</th>
            <th className="py-2 font-medium">Действия</th>
          </tr>
        </thead>
        <tbody>
          {types.map((type) => (
            <tr key={type.slug} className="border-b border-slate-200">
              <td className="py-2 pr-4 font-mono">{type.slug}</td>
              <td className="py-2 pr-4">{type.topic_label}</td>
              <td className="py-2 pr-4">{type.sort_order}</td>
              <td className="py-2 pr-4">{type.is_menu_visible ? 'да' : 'нет'}</td>
              <td className="py-2">
                <button
                  type="button"
                  className="text-slate-700 underline hover:text-slate-900"
                  onClick={() => setModal({ mode: 'edit', slug: type.slug })}
                >
                  Изменить
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {modal ? (
        <PartnerTypeFormModal
          mode={modal.mode}
          slug={modal.slug}
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
