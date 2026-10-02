import { apiErrorMessage, apiFetch } from '../auth/authApi'

export type PlaceCategory = {
  id: string
  slug: string
  label: string
  sort_order: number
}

export type PlaceCategoryInput = {
  slug: string
  label: string
  sort_order: number
}

export type PlaceCategoryUpdate = {
  label: string
  sort_order: number
}

export const placeCategoriesApi = {
  async list(): Promise<PlaceCategory[]> {
    const response = await apiFetch('/api/place-categories')
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось загрузить категории'))
    }
    const data: unknown = await response.json()
    if (!Array.isArray(data)) {
      throw new Error('Не удалось загрузить категории (ответ не список)')
    }
    return data
  },

  async create(input: PlaceCategoryInput): Promise<PlaceCategory> {
    const response = await apiFetch('/api/place-categories', {
      method: 'POST',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Не удалось создать категорию')
    }
    return response.json()
  },

  async update(slug: string, input: PlaceCategoryUpdate): Promise<PlaceCategory> {
    const response = await apiFetch(`/api/place-categories/${encodeURIComponent(slug)}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Не удалось сохранить категорию')
    }
    return response.json()
  },

  async remove(slug: string): Promise<void> {
    const response = await apiFetch(`/api/place-categories/${encodeURIComponent(slug)}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Не удалось удалить категорию')
    }
  },
}
