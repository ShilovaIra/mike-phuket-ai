import { apiFetch } from '../auth/authApi'

export type Partner = {
  id: string
  name: string
  type: string
  referral_url: string
  blurb: string
  logo_path: string
  logo_url: string
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

export type StagedLogo = {
  upload_token: string
  preview_url: string
}

async function detailOr(response: Response, fallback: string): Promise<string> {
  const body: unknown = await response.json().catch(() => null)
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
  }
  return fallback
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

  async uploadLogo(file: File): Promise<StagedLogo> {
    const body = new FormData()
    body.append('file', file)
    const response = await apiFetch('/api/partner-logos/uploads', { method: 'POST', body })
    if (!response.ok) throw new Error(await detailOr(response, 'Не удалось загрузить логотип'))
    return response.json()
  },

  async linkLogo(id: string, uploadToken: string): Promise<Partner> {
    const response = await apiFetch(`/api/partners/${encodeURIComponent(id)}/logo`, {
      method: 'PUT',
      body: JSON.stringify({ upload_token: uploadToken }),
    })
    if (!response.ok) throw new Error(await detailOr(response, 'Не удалось привязать логотип'))
    return response.json()
  },

  async removeLogo(id: string): Promise<Partner> {
    const response = await apiFetch(`/api/partners/${encodeURIComponent(id)}/logo`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error(await detailOr(response, 'Не удалось удалить логотип'))
    return response.json()
  },
}
