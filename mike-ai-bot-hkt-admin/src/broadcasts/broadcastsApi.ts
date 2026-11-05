import { apiErrorMessage, apiFetch } from '../auth/authApi'

export type Broadcast = {
  id: string
  text: string
  scheduled_at: string
  status: 'scheduled' | 'sent'
  button_url: string | null
  button_label: string | null
}

export type BroadcastInput = {
  text: string
  scheduled_at: string
  button_url?: string
  button_label?: string
}

export const broadcastsApi = {
  async list(): Promise<Broadcast[]> {
    const response = await apiFetch('/api/broadcasts')
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось загрузить рассылки'))
    }
    return response.json()
  },

  async create(input: BroadcastInput): Promise<Broadcast> {
    const response = await apiFetch('/api/broadcasts', {
      method: 'POST',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось сохранить рассылку'))
    }
    return response.json()
  },

  async update(id: string, input: BroadcastInput): Promise<Broadcast> {
    const response = await apiFetch(`/api/broadcasts/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось сохранить рассылку'))
    }
    return response.json()
  },

  async remove(id: string): Promise<void> {
    const response = await apiFetch(`/api/broadcasts/${id}`, { method: 'DELETE' })
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось удалить рассылку'))
    }
  },
}
