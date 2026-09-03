import { useEffect, useState, type FormEvent } from 'react'
import { partnersApi, type Partner } from '../partners/partnersApi'
import { partnerUsersApi, type PartnerUserRow } from './partnerUsersApi'

export function PartnerUsersPage() {
  const [users, setUsers] = useState<PartnerUserRow[]>([])
  const [partners, setPartners] = useState<Partner[]>([])
  const [error, setError] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  async function reload() {
    const [userItems, partnerItems] = await Promise.all([
      partnerUsersApi.list(),
      partnersApi.list(),
    ])
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

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Пользователи партнёров</h1>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
        >
          Добавить пользователя
        </button>
      </div>
      {error ? <p role="alert">{error}</p> : null}
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-slate-300">
            <th className="py-2 pr-4 font-medium">Email</th>
            <th className="py-2 pr-4 font-medium">Партнёры</th>
            <th className="py-2 font-medium">Действия</th>
          </tr>
        </thead>
        <tbody>
          {users.map((row) => (
            <tr key={row.id} className="border-b border-slate-200">
              <td className="py-2 pr-4">{row.email}</td>
              <td className="py-2 pr-4">{row.partners.map((p) => p.name).join(', ')}</td>
              <td className="py-2">
                <button
                  type="button"
                  className="text-slate-700 underline hover:text-slate-900"
                  onClick={async () => {
                    await partnerUsersApi.remove(row.id)
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
      {modalOpen ? (
        <CreatePartnerUserModal
          partners={partners}
          onClose={() => setModalOpen(false)}
          onSaved={async () => {
            setModalOpen(false)
            await reload()
          }}
        />
      ) : null}
    </main>
  )
}

function CreatePartnerUserModal({
  partners,
  onClose,
  onSaved,
}: {
  partners: Partner[]
  onClose: () => void
  onSaved: () => void
}) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [selected, setSelected] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (selected.length === 0) {
      setError('Выберите хотя бы одного партнёра')
      return
    }
    try {
      await partnerUsersApi.create({ email, password, partner_ids: selected })
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить')
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
        aria-label="Новый пользователь"
        className="mt-8 w-full max-w-lg rounded-lg bg-white p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-6 text-xl font-semibold tracking-tight">Новый пользователь</h2>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1 text-sm">
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded border border-slate-300 bg-white px-3 py-2"
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Пароль
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded border border-slate-300 bg-white px-3 py-2"
              required
            />
          </label>
          <fieldset className="text-sm">
            <legend className="mb-2">Партнёры</legend>
            {partners.length === 0 ? (
              <p>Нет партнёров. Сначала добавьте их в разделе «Партнёры».</p>
            ) : (
              <div className="flex flex-col gap-2">
                {partners.map((partner) => (
                  <label key={partner.id} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={selected.includes(partner.id)}
                      onChange={(e) => {
                        setSelected((prev) =>
                          e.target.checked
                            ? [...prev, partner.id]
                            : prev.filter((id) => id !== partner.id),
                        )
                      }}
                    />
                    {partner.name}
                  </label>
                ))}
              </div>
            )}
          </fieldset>
          {error ? <p role="alert">{error}</p> : null}
          <div className="flex gap-3">
            <button
              type="submit"
              className="rounded bg-slate-900 px-4 py-2 text-white hover:bg-slate-800"
            >
              Сохранить
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded border border-slate-300 px-4 py-2 hover:bg-slate-50"
            >
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
