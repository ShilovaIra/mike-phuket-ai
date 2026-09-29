import { apiErrorMessage, apiFetch } from '../auth/authApi'

export type Place = {
  id: string
  name: string
  category: string
  blurb: string
  maps_url: string
  partner_id: string | null
  is_active: boolean
  latitude: number
  longitude: number
  photos: { id: string; path: string; url?: string }[]
  cover: string
}

export type StagedPlacePhoto = {
  upload_token: string
  preview_url: string
}

export type PlacePhotoUpdate = {
  upload_token: string
}

export type PlaceInput = {
  name: string
  category: string
  blurb: string
  maps_url: string
  partner_id: string | null
  is_active: boolean
}

export const placesApi = {
  async list(): Promise<Place[]> {
    const response = await apiFetch('/api/places')
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось загрузить места'))
    }
    const data: unknown = await response.json()
    if (!Array.isArray(data)) {
      throw new Error('Не удалось загрузить места (ответ не список)')
    }
    return data
  },

  async create(input: PlaceInput): Promise<Place> {
    const response = await apiFetch('/api/places', {
      method: 'POST',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Не удалось создать место')
    }
    return response.json()
  },

  async update(id: string, input: PlaceInput & { photos?: PlacePhotoUpdate[] }): Promise<Place> {
    const response = await apiFetch(`/api/places/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Не удалось сохранить место')
    }
    return response.json()
  },

  async uploadPhoto(file: File): Promise<StagedPlacePhoto> {
    const body = new FormData()
    body.append('file', file)
    const response = await apiFetch('/api/place-photos/uploads', { method: 'POST', body })
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}))
      throw new Error(
        typeof payload.detail === 'string' ? payload.detail : 'Не удалось загрузить фото',
      )
    }
    return response.json()
  },
}
