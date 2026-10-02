import { useEffect, useRef, useState, type FormEvent } from 'react'
import { partnersApi, type Partner } from '../partners/partnersApi'
import { placeCategoriesApi, type PlaceCategory } from '../place-categories/placeCategoriesApi'
import placeholder from '../assets/placeholders/empty_picture_placeholder.jpg'
import { placesApi, type Place, type PlaceInput } from './placesApi'

const emptyForm: PlaceInput = {
  name: '',
  category: '',
  blurb: '',
  maps_url: '',
  partner_id: null,
  is_active: true,
  mike_recommends: false,
}

type Props = {
  place?: Place
  onClose: () => void
  onSaved: () => void
  onChanged?: () => void | Promise<void>
}

function inputFromPlace(place: Place): PlaceInput {
  return {
    name: place.name,
    category: place.category,
    blurb: place.blurb,
    maps_url: place.maps_url,
    partner_id: place.partner_id,
    is_active: place.is_active,
    mike_recommends: place.mike_recommends,
  }
}

type PhotoState = {
  previewUrl: string
  uploadToken: string | null
  uploading: boolean
  error: string | null
}

const emptyPhoto: PhotoState = { previewUrl: '', uploadToken: null, uploading: false, error: null }
const MAX_PHOTO_BYTES = 5 * 1024 * 1024
const PHOTO_TYPES = ['image/png', 'image/jpeg']

function photoFileProblem(file: File): string | null {
  if (!PHOTO_TYPES.includes(file.type)) return 'Только JPEG или PNG'
  if (file.size > MAX_PHOTO_BYTES) return 'Файл больше 5 МБ'
  return null
}

export function PlaceFormModal({ place, onClose, onSaved, onChanged = () => {} }: Props) {
  const [form, setForm] = useState<PlaceInput>(place ? inputFromPlace(place) : emptyForm)
  const [categories, setCategories] = useState<PlaceCategory[]>([])
  const [partners, setPartners] = useState<Partner[]>([])
  const [error, setError] = useState<string | null>(null)
  const [ready, setReady] = useState(false)
  const [photo, setPhoto] = useState<PhotoState>({
    ...emptyPhoto,
    previewUrl: place?.photos[0]?.url ?? '',
  })
  const [removeSavedPhoto, setRemoveSavedPhoto] = useState(false)
  const [savedId, setSavedId] = useState<string | null>(place?.id ?? null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([placeCategoriesApi.list(), partnersApi.list()])
      .then(([loadedCategories, loadedPartners]) => {
        if (cancelled) return
        setCategories(loadedCategories)
        setPartners(loadedPartners)
        setForm((prev) => ({
          ...prev,
          category: prev.category || loadedCategories[0]?.slug || '',
        }))
        setReady(true)
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message)
          setReady(true)
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  function setField<K extends keyof PlaceInput>(key: K, value: PlaceInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function onPhotoPicked(file: File | undefined) {
    if (!file) return
    const invalid = photoFileProblem(file)
    if (invalid) {
      setPhoto((prev) => ({ ...prev, uploadToken: null, error: invalid }))
      return
    }
    setPhoto((prev) => ({ ...prev, uploading: true, error: null }))
    try {
      const staged = await placesApi.uploadPhoto(file)
      setRemoveSavedPhoto(false)
      setPhoto({
        previewUrl: staged.preview_url,
        uploadToken: staged.upload_token,
        uploading: false,
        error: null,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Не удалось загрузить фото'
      setPhoto((prev) => ({ ...prev, uploading: false, error: message }))
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    try {
      let id = savedId
      if (!id) {
        id = (await placesApi.create(form)).id
        setSavedId(id)
      } else {
        await placesApi.update(id, form)
      }
      await onChanged()
      if (photo.uploadToken) {
        try {
          await placesApi.update(id, {
            ...form,
            photos: [{ upload_token: photo.uploadToken }],
          })
        } catch (err) {
          const reason = err instanceof Error ? err.message : 'Не удалось загрузить фото'
          setError(
            place
              ? `Фото не загрузилось: ${reason}`
              : `Место сохранено, но фото не загрузилось: ${reason}`,
          )
          return
        }
      } else if (removeSavedPhoto) {
        await placesApi.update(id, { ...form, photos: [] })
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
        aria-label={place ? 'Изменить место' : 'Новое место'}
        className="mt-8 w-full max-w-lg rounded-lg bg-white p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="mb-6 text-xl font-semibold tracking-tight">
          {place ? 'Изменить место' : 'Новое место'}
        </h2>
        {!ready ? (
          <p>Загрузка…</p>
        ) : (
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <label className="flex flex-col gap-1 text-sm">
              Название
              <input
                value={form.name}
                onChange={(event) => setField('name', event.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Категория
              <select
                value={form.category}
                onChange={(event) => setField('category', event.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              >
                {categories.map((category) => (
                  <option key={category.slug} value={category.slug}>
                    {category.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Партнёр
              <select
                value={form.partner_id ?? ''}
                onChange={(event) => setField('partner_id', event.target.value || null)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
              >
                <option value="">Без партнёра</option>
                {partners.map((partner) => (
                  <option key={partner.id} value={partner.id}>
                    {partner.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Описание
              <textarea
                value={form.blurb}
                onChange={(event) => setField('blurb', event.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                rows={3}
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Ссылка на карту
              <input
                value={form.maps_url}
                onChange={(event) => setField('maps_url', event.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2"
                required
              />
            </label>
            <div className="flex flex-col gap-2 text-sm">
              <label htmlFor="place-photo">Фото</label>
              <img
                src={photo.previewUrl || placeholder}
                alt="Предпросмотр фото"
                className="h-16 w-16 rounded border border-slate-200 object-cover"
              />
              <input
                ref={fileInputRef}
                id="place-photo"
                type="file"
                accept="image/png,image/jpeg"
                onChange={(event) => {
                  void onPhotoPicked(event.target.files?.[0])
                }}
                disabled={photo.uploading}
                className="sr-only"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={photo.uploading}
                className="self-start rounded border border-slate-300 bg-white px-4 py-2 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {photo.uploading ? 'Загружаем…' : photo.previewUrl ? 'Заменить файл' : 'Выбрать файл'}
              </button>
              {photo.previewUrl ? (
                <button
                  type="button"
                  onClick={() => {
                    setPhoto(emptyPhoto)
                    setRemoveSavedPhoto(Boolean(place?.photos.length))
                  }}
                  className="self-start text-slate-700 underline hover:text-slate-900"
                >
                  Удалить фото
                </button>
              ) : null}
              <p className="text-slate-500">JPEG или PNG, до 5 МБ</p>
              {photo.error ? <p role="alert">{photo.error}</p> : null}
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setField('is_active', event.target.checked)}
              />
              Активно
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Майк рекомендует
              <select
                value={form.mike_recommends ? 'да' : 'нет'}
                onChange={(event) => setField('mike_recommends', event.target.value === 'да')}
                className="rounded border border-slate-300 bg-white px-3 py-2"
              >
                <option value="да">да</option>
                <option value="нет">нет</option>
              </select>
            </label>
            {error ? <p role="alert">{error}</p> : null}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded border border-slate-300 px-3 py-2 text-sm"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={photo.uploading || photo.error !== null}
                className="rounded bg-slate-900 px-3 py-2 text-sm text-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                Сохранить
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
