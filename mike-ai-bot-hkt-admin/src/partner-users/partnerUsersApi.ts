import { apiFetch } from '../auth/authApi'

export type PartnerUserRow = {
  id: string
  email: string
  created_at: string
  partners: { id: string; name: string }[]
}

export type PartnerUserPatch = {
  password?: string
  partner_ids: string[]
}

export type PartnerUserInput = {
  email: string
  password: string
  partner_ids: string[]
}

export const partnerUsersApi = {
  async list(): Promise<PartnerUserRow[]> {
    const response = await apiFetch('/api/partner-users')
    if (!response.ok) throw new Error('Не удалось загрузить пользователей')
    return response.json()
  },

  async create(input: PartnerUserInput): Promise<PartnerUserRow> {
    const response = await apiFetch('/api/partner-users', {
      method: 'POST',
      body: JSON.stringify(input),
    })
    if (!response.ok) throw new Error('Не удалось создать пользователя')
    return response.json()
  },

  async update(id: string, input: PartnerUserPatch): Promise<void> {
    const response = await apiFetch(`/api/partner-users/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    })
    if (!response.ok) throw new Error('Не удалось сохранить пользователя')
  },

  async remove(id: string): Promise<void> {
    const response = await apiFetch(`/api/partner-users/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('Не удалось удалить пользователя')
  },
}
