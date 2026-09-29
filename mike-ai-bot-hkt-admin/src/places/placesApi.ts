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
  photos: { id: string; path: string }[]
  cover: string
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
}
