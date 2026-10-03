import { apiFetch } from '../auth/authApi'

export type KnowledgeBaseEntry = {
  id: string
  partner_id: string | null
  place_id: string | null
  name: string
  kind: string
  blurb: string
  referral_url: string
  maps_url: string
  in_chat: boolean
}

export const knowledgeBaseApi = {
  async list(): Promise<KnowledgeBaseEntry[]> {
    const response = await apiFetch('/api/knowledge-base')
    if (!response.ok) throw new Error('Не удалось загрузить базу знаний')
    return response.json()
  },

  async add(body: { partner_id: string } | { place_id: string }): Promise<KnowledgeBaseEntry> {
    const response = await apiFetch('/api/knowledge-base', {
      method: 'POST',
      body: JSON.stringify(body),
    })
    if (!response.ok) throw new Error('Не удалось добавить в базу знаний')
    return response.json()
  },

  async remove(id: string): Promise<void> {
    const response = await apiFetch(`/api/knowledge-base/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error('Не удалось удалить из базы знаний')
  },
}
