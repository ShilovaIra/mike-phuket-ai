import { apiFetch } from '../auth/authApi'

export type PartnerType = {
  slug: string
  is_menu_visible: boolean
  sort_order: number
  button_label: string
  topic_label: string
  intro: string
  fallback: string
  caption_emoji: string
  caption_cta: string
  button_template: string
}

export const partnerTypesApi = {
  async list(): Promise<PartnerType[]> {
    const response = await apiFetch('/api/partner-types')
    if (!response.ok) throw new Error('Не удалось загрузить типы партнёров')
    return response.json()
  },

  async get(slug: string): Promise<PartnerType | null> {
    const types = await partnerTypesApi.list()
    return types.find((item) => item.slug === slug) ?? null
  },

  async create(input: PartnerType): Promise<PartnerType> {
    const response = await apiFetch('/api/partner-types', {
      method: 'POST',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Не удалось создать тип')
    }
    return response.json()
  },

  async update(slug: string, input: PartnerType): Promise<PartnerType> {
    const response = await apiFetch(`/api/partner-types/${encodeURIComponent(slug)}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Не удалось сохранить тип')
    }
    return response.json()
  },
}
