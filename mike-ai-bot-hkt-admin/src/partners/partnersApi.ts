import { apiFetch } from '../auth/authApi'

export type Partner = {
  id: string
  name: string
  type: string
  referral_url: string
  blurb: string
  logo_path: string
  is_active: boolean
  sort_order: number
}

export type PartnerInput = {
  name: string
  type: string
  referral_url: string
  blurb: string
  is_active: boolean
  sort_order: number
}

export const partnersApi = {
  async list(): Promise<Partner[]> {
    const response = await apiFetch('/api/partners')
    if (!response.ok) throw new Error('Не удалось загрузить партнёров')
    return response.json()
  },

  async get(id: string): Promise<Partner | null> {
    const partners = await partnersApi.list()
    return partners.find((item) => item.id === id) ?? null
  },

  async create(input: PartnerInput): Promise<Partner> {
    const response = await apiFetch('/api/partners', {
      method: 'POST',
      body: JSON.stringify(input),
    })
    if (!response.ok) throw new Error('Не удалось создать партнёра')
    return response.json()
  },

  async update(id: string, input: PartnerInput): Promise<Partner> {
    const response = await apiFetch(`/api/partners/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    })
    if (!response.ok) throw new Error('Не удалось сохранить партнёра')
    return response.json()
  },
}
