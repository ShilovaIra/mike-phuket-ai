import { useEffect, useState, type FormEvent } from 'react'
import { partnerTypesApi, type PartnerType } from '../partner-types/partnerTypesApi'
import { partnersApi, type PartnerInput } from './partnersApi'

const emptyForm: PartnerInput = {
  name: '',
  type: '',
  referral_url: '',
  blurb: '',
  is_active: true,
  sort_order: 0,
}

type Props = {
  mode: 'create' | 'edit'
  partnerId?: string
  types: PartnerType[]
  onClose: () => void
  onSaved: () => void
  onChanged?: () => void
}

type LogoState = {
  previewUrl: string
  uploadToken: string | null
  uploading: boolean
  error: string | null
}

const emptyLogo: LogoState = { previewUrl: '', uploadToken: null, uploading: false, error: null }

const MAX_LOGO_BYTES = 5 * 1024 * 1024
const LOGO_TYPES = ['image/png', 'image/jpeg']

function logoFileProblem(file: File): string | null {
  if (!LOGO_TYPES.includes(file.type)) return 'Только JPEG или PNG'
  if (file.size > MAX_LOGO_BYTES) return 'Файл больше 5 МБ'
  return null
}

export function PartnerFormModal({
  mode,
  partnerId,
  types,
  onClose,
  onSaved,
  onChanged = () => {},
}: Props) {
  const [typeOptions, setTypeOptions] = useState<PartnerType[]>(types)
  const [form, setForm] = useState<PartnerInput>(emptyForm)
  const [logo, setLogo] = useState<LogoState>(emptyLogo)
  const [savedLogoUrl, setSavedLogoUrl] = useState('')
  const [createdId, setCreatedId] = useState<string | undefined>(undefined)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      let loaded = types
      if (loaded.length === 0) {
        try {
          loaded = await partnerTypesApi.list()
        } catch (err) {
          if (!cancelled) {
            setError(err instanceof Error ? err.message : 'Не удалось загрузить типы партнёров')
            setReady(true)
          }
          return
        }
      }
      if (cancelled) return
      setTypeOptions(loaded)

      if (mode === 'edit' && partnerId) {
        const existing = await partnersApi.get(partnerId)
        if (cancelled) return
        if (!existing) {
          setError('Партнёр не найден')
          setReady(true)
          return
        }
        setForm({
          name: existing.name,
          type: existing.type,
          referral_url: existing.referral_url,
          blurb: existing.blurb,
          is_active: existing.is_active,
          sort_order: existing.sort_order,
        })
        setLogo({ ...emptyLogo, previewUrl: existing.logo_url })
        setSavedLogoUrl(existing.logo_url)
      } else {
        setForm({ ...emptyForm })
      }
      setReady(true)
    })()
    return () => {
      cancelled = true
    }
  }, [mode, partnerId, types])

  function setField<K extends keyof PartnerInput>(key: K, value: PartnerInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function onLogoPicked(file: File | undefined) {
    if (!file) return
    const invalid = logoFileProblem(file)
    if (invalid) {
      setLogo((prev) => ({ ...prev, uploadToken: null, error: invalid }))
      return
    }
    setLogo((prev) => ({ ...prev, uploading: true, error: null }))
    try {
      const staged = await partnersApi.uploadLogo(file)
      setLogo({
        previewUrl: staged.preview_url,
        uploadToken: staged.upload_token,
        uploading: false,
        error: null,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Не удалось загрузить логотип'
      setLogo((prev) => ({ ...prev, uploading: false, error: message }))
    }
  }

  async function removeSavedLogo() {
    const id = partnerId ?? createdId
    if (!id) return
    try {
      await partnersApi.removeLogo(id)
      setSavedLogoUrl('')
      setLogo(emptyLogo)
      onChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить логотип')
    }
  }

  function dropPickedLogo() {
    setLogo({ ...emptyLogo, previewUrl: savedLogoUrl })
    setFileInputKey((key) => key + 1)
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      let savedId = partnerId ?? createdId
      if (!savedId) {
        savedId = (await partnersApi.create(form)).id
        setCreatedId(savedId)
        onChanged()
      } else {
        await partnersApi.update(savedId, form)
      }
      if (logo.uploadToken) {
        try {
          await partnersApi.linkLogo(savedId, logo.uploadToken)
        } catch (err) {
          const reason = err instanceof Error ? err.message : 'Не удалось привязать логотип'
          setError(
            mode === 'create'
              ? `Партнёр создан, но логотип не загрузился: ${reason}`
              : `Логотип не загрузился: ${reason}`,
          )
          return
        }
      }
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
        aria-label={mode === 'create' ? 'Новый партнёр' : 'Изменить партнёра'}
        className="mt-8 w-full max-w-2xl rounded-lg bg-white p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-6 text-xl font-semibold tracking-tight">
          {mode === 'create' ? 'Новый партнёр' : 'Изменить партнёра'}
        </h2>
        {!ready ? (
          <p>Загрузка…</p>
        ) : error === 'Партнёр не найден' ? (
          <p role="alert">{error}</p>
        ) : (
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <label className="flex flex-col gap-1 text-sm">
              Имя
              <input
                value={form.name}
                onChange={(e) => setField('name', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Тип
              {typeOptions.length === 0 ? (
                <p role="alert">{error ?? 'Нет типов партнёров. Откройте «Типы партнёров» или обновите страницу.'}</p>
              ) : (
                <select
                  value={form.type}
                  onChange={(e) => setField('type', e.target.value)}
                  className="rounded border border-slate-300 bg-white px-3 py-2"
                  required
                >
                  <option value="" disabled>
                    Выберите тип
                  </option>
                  {typeOptions.map((type) => (
                    <option key={type.slug} value={type.slug}>
                      {type.topic_label}
                    </option>
                  ))}
                </select>
              )}
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Referral URL
              <input
                type="url"
                value={form.referral_url}
                onChange={(e) => setField('referral_url', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Описание
              <textarea
                value={form.blurb}
                onChange={(e) => setField('blurb', e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                rows={3}
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Порядок
              <input
                type="number"
                value={form.sort_order}
                onChange={(e) => setField('sort_order', Number(e.target.value))}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <div className="flex flex-col gap-2 text-sm">
              <label htmlFor="partner-logo">Логотип</label>
              <div className="flex items-center gap-4">
                {logo.previewUrl ? (
                  <img
                    src={logo.previewUrl}
                    alt="Предпросмотр логотипа"
                    className="h-16 w-16 rounded border border-slate-200 object-contain"
                  />
                ) : null}
                <input
                  key={fileInputKey}
                  id="partner-logo"
                  type="file"
                  accept="image/png,image/jpeg"
                  onChange={(e) => onLogoPicked(e.target.files?.[0])}
                  disabled={logo.uploading}
                />
                {logo.uploadToken || logo.error ? (
                  <button
                    type="button"
                    onClick={dropPickedLogo}
                    className="text-slate-700 underline hover:text-slate-900"
                  >
                    Убрать файл
                  </button>
                ) : savedLogoUrl ? (
                  <button
                    type="button"
                    onClick={removeSavedLogo}
                    className="text-red-700 underline hover:text-red-900"
                  >
                    Удалить логотип
                  </button>
                ) : null}
              </div>
              <p className="text-slate-500">JPEG или PNG, до 5 МБ</p>
              {logo.uploading ? <p role="status">Загружаем…</p> : null}
              {logo.error ? <p role="alert">{logo.error}</p> : null}
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => setField('is_active', e.target.checked)}
              />
              Активен
            </label>
            {error && error !== 'Партнёр не найден' ? <p role="alert">{error}</p> : null}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={logo.uploading || logo.error !== null}
                className="rounded bg-slate-900 px-4 py-2 text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
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
        )}
      </div>
    </div>
  )
}
