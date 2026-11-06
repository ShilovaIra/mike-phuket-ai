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

export type BroadcastListMessage = {
  id: string
  text: string
  button_url: string | null
  button_label: string | null
}

export type BroadcastList = {
  id: string
  name: string
  messages: BroadcastListMessage[]
}

export type IntervalBroadcast = {
  id: string
  list_id: string
  list_name: string
  interval_days: number
  scheduled_at: string
  next_message: BroadcastListMessage | null
}

export const broadcastListsApi = {
  async list(): Promise<BroadcastList[]> {
    const response = await apiFetch('/api/broadcast-lists')
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось загрузить списки'))
    }
    return response.json()
  },

  async create(name: string): Promise<BroadcastList> {
    const response = await apiFetch('/api/broadcast-lists', {
      method: 'POST',
      body: JSON.stringify({ name }),
    })
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось сохранить список'))
    }
    return response.json()
  },

  async addMessage(
    listId: string,
    input: { text: string; button_url?: string; button_label?: string },
  ): Promise<BroadcastListMessage> {
    const response = await apiFetch(`/api/broadcast-lists/${listId}/messages`, {
      method: 'POST',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось сохранить сообщение'))
    }
    return response.json()
  },

  async moveMessage(listId: string, messageId: string, direction: 'up' | 'down'): Promise<void> {
    const response = await apiFetch(
      `/api/broadcast-lists/${listId}/messages/${messageId}/move`,
      {
        method: 'POST',
        body: JSON.stringify({ direction }),
      },
    )
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось переместить сообщение'))
    }
  },
}

export const intervalBroadcastsApi = {
  async list(): Promise<IntervalBroadcast[]> {
    const response = await apiFetch('/api/interval-broadcasts')
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось загрузить рассылки'))
    }
    return response.json()
  },

  async create(input: {
    list_id: string
    scheduled_at: string
    interval_days: number
  }): Promise<IntervalBroadcast> {
    const response = await apiFetch('/api/interval-broadcasts', {
      method: 'POST',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось сохранить рассылку'))
    }
    return response.json()
  },

  async update(
    id: string,
    input: { scheduled_at?: string; interval_days?: number },
  ): Promise<IntervalBroadcast> {
    const response = await apiFetch(`/api/interval-broadcasts/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось сохранить рассылку'))
    }
    return response.json()
  },

  async remove(id: string): Promise<void> {
    const response = await apiFetch(`/api/interval-broadcasts/${id}`, { method: 'DELETE' })
    if (!response.ok) {
      throw new Error(await apiErrorMessage(response, 'Не удалось удалить рассылку'))
    }
  },
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
