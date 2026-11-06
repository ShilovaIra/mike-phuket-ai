import { useEffect, useState, type FormEvent } from 'react'
import {
  broadcastListsApi,
  intervalBroadcastsApi,
  type BroadcastList,
  type IntervalBroadcast,
} from './broadcastsApi'

function bangkokTimestamp(localValue: string): string {
  return `${localValue}:00+07:00`
}

export function IntervalBroadcastsPanel() {
  const [lists, setLists] = useState<BroadcastList[]>([])
  const [schedules, setSchedules] = useState<IntervalBroadcast[]>([])
  const [listName, setListName] = useState('')
  const [messageText, setMessageText] = useState<Record<string, string>>({})
  const [messageUrl, setMessageUrl] = useState<Record<string, string>>({})
  const [messageLabel, setMessageLabel] = useState<Record<string, string>>({})
  const [listId, setListId] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')
  const [intervalDays, setIntervalDays] = useState('3')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function reload() {
    const [nextLists, nextSchedules] = await Promise.all([
      broadcastListsApi.list(),
      intervalBroadcastsApi.list(),
    ])
    setLists(nextLists)
    setSchedules(nextSchedules)
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

  async function onCreateList(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await broadcastListsApi.create(listName)
      setListName('')
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить список')
    }
  }

  async function onAddMessage(event: FormEvent, id: string) {
    event.preventDefault()
    setError(null)
    try {
      await broadcastListsApi.addMessage(id, {
        text: messageText[id] ?? '',
        button_url: messageUrl[id] ?? '',
        button_label: messageLabel[id] ?? '',
      })
      setMessageText((current) => ({ ...current, [id]: '' }))
      setMessageUrl((current) => ({ ...current, [id]: '' }))
      setMessageLabel((current) => ({ ...current, [id]: '' }))
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить сообщение')
    }
  }

  async function onSaveSchedule(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      if (editingId) {
        await intervalBroadcastsApi.update(editingId, {
          scheduled_at: bangkokTimestamp(scheduledAt),
          interval_days: Number(intervalDays),
        })
      } else {
        await intervalBroadcastsApi.create({
          list_id: listId,
          scheduled_at: bangkokTimestamp(scheduledAt),
          interval_days: Number(intervalDays),
        })
      }
      setEditingId(null)
      setListId('')
      setScheduledAt('')
      setIntervalDays('3')
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить рассылку')
    }
  }

  return (
    <div>
      <form onSubmit={onCreateList} className="mb-8 flex max-w-xl flex-col gap-3">
        <label className="flex flex-col gap-1 text-sm">
          Название списка
          <input
            className="rounded border border-slate-300 px-3 py-2"
            value={listName}
            onChange={(event) => setListName(event.target.value)}
            required
          />
        </label>
        <button
          type="submit"
          className="w-fit rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
        >
          Сохранить список
        </button>
      </form>
      <ul className="mb-10 flex flex-col gap-6">
        {lists.map((list) => (
          <li key={list.id}>
            <h2 className="mb-2 text-lg font-medium">{list.name}</h2>
            <ul className="mb-3 flex flex-col gap-2">
              {list.messages.map((message, index) => (
                <li key={message.id}>
                  <span>{message.text}</span>
                  {message.button_label ? (
                    <span className="ml-2">{message.button_label}</span>
                  ) : null}
                  {index > 0 ? (
                    <button
                      type="button"
                      className="ml-3 text-sm underline"
                      onClick={() => {
                        void broadcastListsApi
                          .moveMessage(list.id, message.id, 'up')
                          .then(reload)
                          .catch((err: Error) => setError(err.message))
                      }}
                    >
                      Вверх
                    </button>
                  ) : null}
                  {index < list.messages.length - 1 ? (
                    <button
                      type="button"
                      className="ml-2 text-sm underline"
                      onClick={() => {
                        void broadcastListsApi
                          .moveMessage(list.id, message.id, 'down')
                          .then(reload)
                          .catch((err: Error) => setError(err.message))
                      }}
                    >
                      Вниз
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
            <form
              onSubmit={(event) => onAddMessage(event, list.id)}
              className="flex max-w-xl flex-col gap-3"
            >
              <label className="flex flex-col gap-1 text-sm">
                Текст сообщения
                <textarea
                  className="rounded border border-slate-300 px-3 py-2"
                  value={messageText[list.id] ?? ''}
                  onChange={(event) =>
                    setMessageText((current) => ({ ...current, [list.id]: event.target.value }))
                  }
                  required
                />
              </label>
              <label className="flex flex-col gap-1 text-sm">
                Ссылка на карты
                <input
                  className="rounded border border-slate-300 px-3 py-2"
                  value={messageUrl[list.id] ?? ''}
                  onChange={(event) =>
                    setMessageUrl((current) => ({ ...current, [list.id]: event.target.value }))
                  }
                />
              </label>
              <label className="flex flex-col gap-1 text-sm">
                Текст кнопки
                <input
                  className="rounded border border-slate-300 px-3 py-2"
                  value={messageLabel[list.id] ?? ''}
                  onChange={(event) =>
                    setMessageLabel((current) => ({ ...current, [list.id]: event.target.value }))
                  }
                />
              </label>
              <button
                type="submit"
                className="w-fit rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
              >
                Добавить сообщение
              </button>
            </form>
          </li>
        ))}
      </ul>
      <form onSubmit={onSaveSchedule} className="mb-8 flex max-w-xl flex-col gap-3">
        <label className="flex flex-col gap-1 text-sm">
          Список
          <select
            className="rounded border border-slate-300 px-3 py-2"
            value={listId}
            onChange={(event) => setListId(event.target.value)}
            required={!editingId}
            disabled={Boolean(editingId)}
          >
            <option value="">Выберите список</option>
            {lists.map((list) => (
              <option key={list.id} value={list.id}>
                {list.name}
              </option>
            ))}
          </select>
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
          Интервал (дней)
          <input
            type="number"
            min={1}
            className="rounded border border-slate-300 px-3 py-2"
            value={intervalDays}
            onChange={(event) => setIntervalDays(event.target.value)}
            required
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
        {schedules.map((item) => (
          <li key={item.id}>
            <span>{item.list_name}</span>
            <span className="ml-3">каждые {item.interval_days} дн.</span>
            <span className="ml-3">{item.scheduled_at}</span>
            {item.next_message ? <span className="ml-3">{item.next_message.text}</span> : null}
            <button
              type="button"
              className="ml-3 text-sm underline"
              onClick={() => {
                setEditingId(item.id)
                setListId(item.list_id)
                setScheduledAt(item.scheduled_at.slice(0, 16))
                setIntervalDays(String(item.interval_days))
              }}
            >
              Изменить
            </button>
            <button
              type="button"
              className="ml-2 text-sm underline"
              onClick={() => {
                void intervalBroadcastsApi
                  .remove(item.id)
                  .then(reload)
                  .catch((err: Error) => setError(err.message))
              }}
            >
              Удалить
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
