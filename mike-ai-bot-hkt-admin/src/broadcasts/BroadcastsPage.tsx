import { useEffect, useState, type FormEvent } from 'react'
import { IntervalBroadcastsPanel } from './IntervalBroadcastsPanel'
import { broadcastsApi, type Broadcast } from './broadcastsApi'

function bangkokTimestamp(localValue: string): string {
  return `${localValue}:00+07:00`
}

type Tab = 'one-time' | 'interval'

export function BroadcastsPage() {
  const [tab, setTab] = useState<Tab>('one-time')
  const [items, setItems] = useState<Broadcast[]>([])
  const [editingId, setEditingId] = useState<string | null>(null)
  const [text, setText] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')
  const [buttonUrl, setButtonUrl] = useState('')
  const [buttonLabel, setButtonLabel] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function reload() {
    setItems(await broadcastsApi.list())
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

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      const input = {
        text,
        scheduled_at: bangkokTimestamp(scheduledAt),
        button_url: buttonUrl,
        button_label: buttonLabel,
      }
      if (editingId) {
        await broadcastsApi.update(editingId, input)
      } else {
        await broadcastsApi.create(input)
      }
      setEditingId(null)
      setText('')
      setScheduledAt('')
      setButtonUrl('')
      setButtonLabel('')
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить рассылку')
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Рассылка</h1>
      <div role="tablist" className="mb-6 flex gap-1 border-b border-slate-300">
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'one-time'}
          className={`-mb-px border-b-2 px-4 py-2 text-sm ${
            tab === 'one-time'
              ? 'border-slate-900 font-medium text-slate-900'
              : 'border-transparent text-slate-500'
          }`}
          onClick={() => setTab('one-time')}
        >
          Разовые
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'interval'}
          className={`-mb-px border-b-2 px-4 py-2 text-sm ${
            tab === 'interval'
              ? 'border-slate-900 font-medium text-slate-900'
              : 'border-transparent text-slate-500'
          }`}
          onClick={() => setTab('interval')}
        >
          Интервал
        </button>
      </div>
      {tab === 'interval' ? (
        <IntervalBroadcastsPanel />
      ) : (
        <>
          <form onSubmit={onSubmit} className="mb-8 flex max-w-xl flex-col gap-3">
            <label className="flex flex-col gap-1 text-sm">
              Текст сообщения
              <textarea
                className="rounded border border-slate-300 px-3 py-2"
                value={text}
                onChange={(event) => setText(event.target.value)}
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Дата и время (Бангкок)
              <input
                type="datetime-local"
                className="rounded border border-slate-300 px-3 py-2"
                value={scheduledAt}
                onChange={(event) => setScheduledAt(event.target.value)}
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Ссылка на карты
              <input
                className="rounded border border-slate-300 px-3 py-2"
                value={buttonUrl}
                onChange={(event) => setButtonUrl(event.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Текст кнопки
              <input
                className="rounded border border-slate-300 px-3 py-2"
                value={buttonLabel}
                onChange={(event) => setButtonLabel(event.target.value)}
              />
            </label>
            {error ? <p className="text-sm text-red-700">{error}</p> : null}
            <button
              type="submit"
              className="w-fit rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
            >
              Сохранить
            </button>
          </form>
          <ul className="flex flex-col gap-2">
            {items.map((item) => (
              <li
                key={item.id}
                className={item.status === 'sent' ? 'text-slate-400' : undefined}
              >
                <span>{item.scheduled_at}</span>
                <span className="ml-3">{item.text}</span>
                {item.button_label ? <span className="ml-2">{item.button_label}</span> : null}
                {item.status === 'scheduled' ? (
                  <span className="ml-3">
                    <button
                      type="button"
                      className="text-sm underline"
                      onClick={() => {
                        setEditingId(item.id)
                        setText(item.text)
                        setScheduledAt(item.scheduled_at.slice(0, 16))
                        setButtonUrl(item.button_url ?? '')
                        setButtonLabel(item.button_label ?? '')
                      }}
                    >
                      Изменить
                    </button>
                    <button
                      type="button"
                      className="ml-2 text-sm underline"
                      onClick={() => {
                        void broadcastsApi.remove(item.id).then(reload).catch((err: Error) => {
                          setError(err.message)
                        })
                      }}
                    >
                      Удалить
                    </button>
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        </>
      )}
    </main>
  )
}
