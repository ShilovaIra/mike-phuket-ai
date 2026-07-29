import { apiFetch } from '../auth/authApi'

export type TopicCount = {
  unique_users: number
  taps: number
}

export type BotStats = {
  total_users: number
  new_users_today: number
  active_today: number
  new_users_7d: number
  topics_all_time: Record<string, TopicCount>
  topics_7d: Record<string, TopicCount>
  leads_all_time: number
  leads_7d: number
  users_by_first_source: Record<string, number>
}

export const statsApi = {
  async get(): Promise<BotStats> {
    const response = await apiFetch('/api/stats')
    if (!response.ok) throw new Error('Не удалось загрузить статистику')
    return response.json()
  },
}
