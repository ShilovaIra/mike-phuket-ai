import { apiFetch } from '../auth/authApi'

export type TopicStat = {
  slug: string
  label: string
  unique_users: number
  taps: number
}

export type BotStats = {
  total_users: number
  new_users_today: number
  active_today: number
  new_users_7d: number
  topics_all_time: TopicStat[]
  topics_7d: TopicStat[]
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
