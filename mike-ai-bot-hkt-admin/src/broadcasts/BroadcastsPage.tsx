import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { IntervalBroadcastsPanel } from './IntervalBroadcastsPanel'
import { broadcastsApi, type Broadcast } from './broadcastsApi'
import { formatBangkok } from './formatBangkok'
import { Icon } from '../shell/icons'

function bangkokTimestamp(localValue: string): string {
  return `${localValue}:00+07:00`
}

type Tab = 'one-time' | 'interval'

const TELEGRAM_LIMIT = 4096

export function BroadcastsPage() {
  const [tab, setTab] = useState<Tab>('one-time')
  const [items, setItems] = useState<Broadcast[]>([])
  const [loading, setLoading] = useState(true)
  const [showAll, setShowAll] = useState(false)
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
    reload()
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
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

  function cancelEdit() {
    setEditingId(null)
    setText('')
    setScheduledAt('')
    setButtonUrl('')
    setButtonLabel('')
  }

  const ordered = useMemo(
    () => [...items].sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at)),
    [items],
  )
  const sentCount = items.filter((item) => item.status === 'sent').length
  const queuedCount = items.filter((item) => item.status === 'scheduled').length
  const nextId =
    ordered.find((item) => item.status === 'scheduled')?.id ?? null
  const visible = showAll ? ordered : ordered.slice(0, 6)

  return (
    <main className={tab === 'one-time' ? 'cast cast--once' : 'cast'}>
      <header className="cast-head">
        <h1>Рассылка</h1>
        <p>Отправляйте разовые сообщения или настраивайте цепочки с интервалом</p>
      </header>
      <div role="tablist" aria-label="Тип рассылки" className="cast-tabs">
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'one-time'}
          className={`cast-tab${tab === 'one-time' ? ' is-active' : ''}`}
          onClick={() => setTab('one-time')}
        >
          <Icon name="send" size={16} />
          Разовая
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'interval'}
          className={`cast-tab${tab === 'interval' ? ' is-active' : ''}`}
          onClick={() => setTab('interval')}
        >
          <Icon name="calendar" size={16} />
          Интервал
        </button>
      </div>

      {tab === 'interval' ? (
        <IntervalBroadcastsPanel />
      ) : (
        <>
          <section className="cast-stats" aria-label="Сводка разовых">
            <article className="glass-pane cast-stat">
              <span className="cast-stat__icon">
                <Icon name="send" />
              </span>
              <div>
                <strong>{loading ? '—' : sentCount}</strong>
                <span>Отправлено</span>
              </div>
            </article>
            <article className="glass-pane cast-stat">
              <span className="cast-stat__icon">
                <Icon name="clock" />
              </span>
              <div>
                <strong>{loading ? '—' : queuedCount}</strong>
                <span>В очереди</span>
              </div>
            </article>
          </section>

          <section className="glass-pane cast-card">
            <form onSubmit={onSubmit} className="cast-form">
              <label className="cast-label">
                <span>
                  Текст сообщения <span className="req">*</span>
                </span>
                <span className="ta-wrap">
                  <textarea
                    className="glass-field"
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                    placeholder="Введите текст рассылки…"
                    maxLength={TELEGRAM_LIMIT}
                    required
                  />
                  <span className="ta-count">
                    {text.length} / {TELEGRAM_LIMIT}
                  </span>
                </span>
              </label>
              <label className="cast-row">
                <span>
                  Дата и время (Бангкок) <span className="req">*</span>
                </span>
                <input
                  type="datetime-local"
                  className="glass-field"
                  value={scheduledAt}
                  onChange={(event) => setScheduledAt(event.target.value)}
                  required
                />
              </label>
              <label className="cast-row">
                <span>Ссылка</span>
                <span className="cast-input-wrap">
                  <span className="cast-input-icon">
                    <Icon name="link" size={16} />
                  </span>
                  <input
                    className="glass-field"
                    value={buttonUrl}
                    onChange={(event) => setButtonUrl(event.target.value)}
                    placeholder="https://… (опционально)"
                    inputMode="url"
                  />
                </span>
              </label>
              <label className="cast-row">
                <span>Текст кнопки</span>
                <input
                  className="glass-field"
                  value={buttonLabel}
                  onChange={(event) => setButtonLabel(event.target.value)}
                  placeholder="Например: Открыть"
                />
              </label>
              {error ? (
                <p className="form-error" role="alert">
                  {error}
                </p>
              ) : null}
              <div className="cast-actions">
                <button type="submit" className="ice-button">
                  <Icon name="send" size={16} />
                  Сохранить
                </button>
                {editingId ? (
                  <button type="button" className="ghost-button" onClick={cancelEdit}>
                    Отменить
                  </button>
                ) : null}
              </div>
            </form>
          </section>

          <section className="glass-pane cast-card">
            <div className="card-head">
              <h2>Последние рассылки</h2>
              {ordered.length > 6 ? (
                <button type="button" className="linkish" onClick={() => setShowAll((value) => !value)}>
                  {showAll ? 'Свернуть' : 'Смотреть все'}
                </button>
              ) : null}
            </div>
            {loading ? <p className="empty-copy">Загрузка…</p> : null}
            {!loading && ordered.length === 0 ? (
              <p className="empty-copy">
                Пока пусто. Напишите текст и время — сообщение появится в очереди.
              </p>
            ) : null}
            <ul className="queue">
              {visible.map((item) => {
                const sent = item.status === 'sent'
                return (
                  <li
                    key={item.id}
                    className={`queue-row${item.id === nextId ? ' is-next' : ''}${sent ? ' text-slate-400' : ''}`}
                  >
                    <span
                      className="queue-mark"
                      role="img"
                      aria-label={sent ? 'Отправлено' : 'Запланировано'}
                    >
                      <Icon name={sent ? 'check' : 'clock'} size={16} />
                    </span>
                    <div>
                      <p className="queue-text">{item.text}</p>
                      {item.button_label ? <p className="queue-meta">{item.button_label}</p> : null}
                      <div className="queue-actions">
                        {sent ? null : (
                          <button
                            type="button"
                            className="linkish"
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
                        )}
                        <button
                          type="button"
                          className="linkish"
                          onClick={() => {
                            void broadcastsApi
                              .remove(item.id)
                              .then(reload)
                              .catch((err: Error) => setError(err.message))
                          }}
                        >
                          Удалить
                        </button>
                      </div>
                    </div>
                    <time className="queue-time" dateTime={item.scheduled_at}>
                      {formatBangkok(item.scheduled_at)}
                    </time>
                  </li>
                )
              })}
            </ul>
          </section>
        </>
      )}
    </main>
  )
}
