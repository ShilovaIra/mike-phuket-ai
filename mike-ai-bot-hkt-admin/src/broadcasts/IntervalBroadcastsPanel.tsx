import { useEffect, useState, type FormEvent } from 'react'
import {
  broadcastListsApi,
  intervalBroadcastsApi,
  type BroadcastList,
  type BroadcastListMessage,
  type IntervalBroadcast,
} from './broadcastsApi'
import { chainDelay, daysLabel, formatBangkok } from './formatBangkok'
import { Icon } from '../shell/icons'

function bangkokTimestamp(localValue: string): string {
  return `${localValue}:00+07:00`
}

const TELEGRAM_LIMIT = 4096
const HISTORY_PREVIEW = 4

export function IntervalBroadcastsPanel() {
  const [lists, setLists] = useState<BroadcastList[]>([])
  const [schedules, setSchedules] = useState<IntervalBroadcast[]>([])
  const [loading, setLoading] = useState(true)
  const [showAll, setShowAll] = useState(false)
  const [listName, setListName] = useState('')
  const [listId, setListId] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [composing, setComposing] = useState(true)
  const [draftText, setDraftText] = useState('')
  const [draftUrl, setDraftUrl] = useState('')
  const [draftLabel, setDraftLabel] = useState('')
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
    return nextLists
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

  useEffect(() => {
    if (lists.length === 0) {
      setListId('')
      return
    }
    if (!lists.some((list) => list.id === listId)) {
      setListId(lists[0].id)
    }
  }, [lists, listId])

  const list = lists.find((item) => item.id === listId) ?? null

  useEffect(() => {
    if (!list) {
      setSelectedId(null)
      return
    }
    if (selectedId && list.messages.some((message) => message.id === selectedId)) return
    const first = list.messages[0]?.id ?? null
    setSelectedId(first)
    setComposing(first === null)
  }, [list, selectedId])

  const selected = list?.messages.find((message) => message.id === selectedId) ?? null
  const savedSchedule = schedules.find((item) => item.list_id === listId) ?? null
  const editorText = composing ? draftText : (selected?.text ?? '')
  const editorUrl = composing ? draftUrl : (selected?.button_url ?? '')
  const editorLabel = composing ? draftLabel : (selected?.button_label ?? '')
  const history = showAll ? schedules : schedules.slice(0, HISTORY_PREVIEW)

  function startDraft() {
    setComposing(true)
    setDraftText('')
    setDraftUrl('')
    setDraftLabel('')
  }

  function showMessage(message: BroadcastListMessage) {
    setComposing(false)
    setSelectedId(message.id)
  }

  async function onCreateList(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      const created = await broadcastListsApi.create(listName)
      setListName('')
      await reload()
      setListId(created.id)
      setComposing(true)
      setSelectedId(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить список')
    }
  }

  async function onAddMessage(event: FormEvent) {
    event.preventDefault()
    if (!composing || !list) return
    setError(null)
    try {
      const created = await broadcastListsApi.addMessage(list.id, {
        text: draftText,
        button_url: draftUrl,
        button_label: draftLabel,
      })
      setComposing(false)
      setSelectedId(created.id)
      setDraftText('')
      setDraftUrl('')
      setDraftLabel('')
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
      setScheduledAt('')
      setIntervalDays('3')
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить рассылку')
    }
  }

  async function move(messageId: string, direction: 'up' | 'down') {
    if (!list) return
    setError(null)
    try {
      await broadcastListsApi.moveMessage(list.id, messageId, direction)
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось переместить сообщение')
    }
  }

  async function removeList() {
    if (!list) return
    setError(null)
    try {
      await broadcastListsApi.remove(list.id)
      setListId('')
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить список')
    }
  }

  return (
    <div className="interval-layout">
      <div className="interval-col">
        <section className="glass-pane chain-card">
          <div className="card-head">
            <div>
              <div className="pane-kicker">
                <Icon name="layers" size={18} />
                <h2 className="pane-title">Цепочка сообщений</h2>
              </div>
              <p className="pane-help">
                {list ? (
                  <>
                    <span>{list.name}</span>
                    <span> — добавьте сообщения и задайте их порядок.</span>
                  </>
                ) : (
                  'Несколько сообщений уходят по очереди с одним интервалом.'
                )}
              </p>
            </div>
          </div>
          {loading ? <p className="empty-copy">Загрузка…</p> : null}
          {!loading && !list ? (
            <p className="empty-copy">Сначала сохраните список справа — цепочка появится здесь.</p>
          ) : null}
          {!loading && list && list.messages.length === 0 ? (
            <p className="empty-copy">В этом списке пока нет сообщений.</p>
          ) : null}
          <ul className="chain-list">
            {list?.messages.map((message, index) => {
              const firstLine = message.text.split('\n')[0] ?? message.text
              const extra = message.button_label
              return (
                <li
                  key={message.id}
                  className={`chain-row${message.id === selectedId && !composing ? ' is-selected' : ''}`}
                >
                  <div className="chain-moves">
                    <button
                      type="button"
                      aria-label="Вверх"
                      disabled={index === 0}
                      onClick={() => void move(message.id, 'up')}
                    >
                      <Icon name="chevronUp" size={14} />
                    </button>
                    <button
                      type="button"
                      aria-label="Вниз"
                      disabled={index === list.messages.length - 1}
                      onClick={() => void move(message.id, 'down')}
                    >
                      <Icon name="chevronDown" size={14} />
                    </button>
                  </div>
                  <button type="button" className="chain-pick" onClick={() => showMessage(message)}>
                    <span className="chain-num">{index + 1}</span>
                    <span className="chain-copy">
                      <strong>{firstLine}</strong>
                      {extra ? <span>{extra}</span> : null}
                    </span>
                  </button>
                  <span className="chain-when">
                    <Icon name="clock" size={14} />
                    {chainDelay(index, savedSchedule?.interval_days ?? null)}
                  </span>
                </li>
              )
            })}
          </ul>
          <button type="button" className="ghost-button" onClick={startDraft} disabled={!list}>
            <Icon name="plus" size={16} />
            Добавить сообщение
          </button>
        </section>

        <section className="glass-pane editor-card">
          <div className="pane-kicker">
            <Icon name="send" size={18} />
            <h2 className="pane-title">
              {composing || !selected ? 'Новое сообщение' : 'Редактирование сообщения'}
            </h2>
          </div>
          <div className="editor-grid">
            <form id="chain-draft" onSubmit={onAddMessage} className="editor-fields">
              <label className="cast-label">
                <span>
                  Текст сообщения <span className="req">*</span>
                </span>
                <span className="ta-wrap">
                  <textarea
                    className="glass-field"
                    value={editorText}
                    onChange={(event) => setDraftText(event.target.value)}
                    readOnly={!composing}
                    maxLength={TELEGRAM_LIMIT}
                    required={composing}
                  />
                  <span className="ta-count">
                    {editorText.length} / {TELEGRAM_LIMIT}
                  </span>
                </span>
              </label>
              <div className="field-pair">
                <label className="cast-label">
                  Ссылка
                  <span className="cast-input-wrap">
                    <span className="cast-input-icon">
                      <Icon name="link" size={16} />
                    </span>
                    <input
                      className="glass-field"
                      value={editorUrl}
                      onChange={(event) => setDraftUrl(event.target.value)}
                      readOnly={!composing}
                      placeholder="https://…"
                      inputMode="url"
                    />
                  </span>
                </label>
                <label className="cast-label">
                  Текст кнопки
                  <input
                    className="glass-field"
                    value={editorLabel}
                    onChange={(event) => setDraftLabel(event.target.value)}
                    readOnly={!composing}
                    placeholder="Открыть"
                  />
                </label>
              </div>
              {!composing && selected ? (
                <p className="editor-hint">
                  Строки в цепочке только для чтения. Новое сообщение добавляется кнопкой выше.
                </p>
              ) : null}
            </form>
            <aside className="tg-preview" aria-label="Предпросмотр Telegram">
              <p>Предпросмотр (Telegram)</p>
              <div className="tg-bubble">
                <strong>{editorText.trim() || 'Текст появится здесь'}</strong>
                {editorLabel.trim() || editorUrl.trim() ? (
                  <span>{editorLabel.trim() || 'Открыть'}</span>
                ) : null}
              </div>
            </aside>
          </div>
          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
          <div className="cast-actions editor-actions">
            <button
              type="submit"
              form="chain-draft"
              className="ice-button"
              disabled={!composing || !list || draftText.trim().length === 0}
            >
              Сохранить цепочку
            </button>
            <button
              type="submit"
              form="interval-schedule"
              className="ghost-button"
              disabled={!listId}
            >
              <Icon name="play" size={16} />
              {editingId ? 'Сохранить расписание' : 'Запустить рассылку'}
            </button>
            {editingId ? (
              <button
                type="button"
                className="ghost-button"
                onClick={() => {
                  setEditingId(null)
                  setScheduledAt('')
                  setIntervalDays('3')
                }}
              >
                Отменить
              </button>
            ) : null}
          </div>
        </section>
      </div>

      <div className="interval-col">
        <section className="glass-pane settings-card">
          <div className="pane-kicker">
            <Icon name="calendar" size={18} />
            <h2 className="pane-title">Общие настройки</h2>
          </div>
          <form id="interval-schedule" onSubmit={onSaveSchedule} className="settings-form">
            <label className="cast-label">
              <span>
                Список сообщений <span className="req">*</span>
              </span>
              <select
                className="glass-field"
                value={listId}
                onChange={(event) => {
                  setListId(event.target.value)
                  setComposing(false)
                  setEditingId(null)
                }}
                required={!editingId}
                disabled={Boolean(editingId) || lists.length === 0}
              >
                <option value="">Выберите список</option>
                {lists.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="cast-label">
              Дата и время начала (Бангкок)
              <input
                type="datetime-local"
                className="glass-field"
                value={scheduledAt}
                onChange={(event) => setScheduledAt(event.target.value)}
                required
              />
            </label>
            <label className="cast-label">
              Интервал между сообщениями
              <span className="interval-step">
                <input
                  type="number"
                  min={1}
                  className="glass-field"
                  value={intervalDays}
                  onChange={(event) => setIntervalDays(event.target.value)}
                  required
                />
                <span>{daysLabel(Number(intervalDays) || 0)}</span>
              </span>
            </label>
            <p className="editor-hint">
              Первое уходит в указанное время, каждое следующее — через этот интервал.
            </p>
          </form>
          <form onSubmit={onCreateList} className="quiet-create">
            <label className="cast-label">
              Новый список
              <input
                className="glass-field"
                value={listName}
                onChange={(event) => setListName(event.target.value)}
                required
              />
            </label>
            <div className="cast-actions">
              <button type="submit" className="ghost-button">
                Сохранить список
              </button>
              {list ? (
                <button type="button" className="ghost-button" onClick={() => void removeList()}>
                  Удалить список
                </button>
              ) : null}
            </div>
          </form>
        </section>

        <section className="glass-pane history-card">
          <div className="card-head">
            <div className="pane-kicker">
              <Icon name="clock" size={18} />
              <h2 className="pane-title">История рассылок</h2>
            </div>
            {schedules.length > HISTORY_PREVIEW ? (
              <button type="button" className="linkish" onClick={() => setShowAll((value) => !value)}>
                {showAll ? 'Свернуть' : 'Смотреть все'}
              </button>
            ) : null}
          </div>
          {!loading && schedules.length === 0 ? (
            <p className="empty-copy">
              Расписаний пока нет. Выберите список, время и интервал, затем запустите рассылку.
            </p>
          ) : null}
          <ul className="history-list">
            {history.map((item) => (
              <li key={item.id} className="history-row">
                <span className="queue-mark" role="img" aria-label="Запланировано">
                  <Icon name="clock" size={16} />
                </span>
                <div>
                  <p>{item.next_message?.text ?? item.list_name}</p>
                  <p className="queue-meta">
                    Список: {item.list_name} · каждые {item.interval_days} {daysLabel(item.interval_days)}
                  </p>
                  <div className="queue-actions">
                    <button
                      type="button"
                      className="linkish"
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
                      className="linkish"
                      onClick={() => {
                        void intervalBroadcastsApi
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
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
