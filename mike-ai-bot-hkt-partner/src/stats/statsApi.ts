import { apiFetch } from '../auth/authApi'

export type PartnerRef = {
  id: string
  name: string
}

export type PartnerMe = {
  email: string
  partners: PartnerRef[]
}

export type PeriodStats = {
  views: number
  referral_clicks: number
  opened_views: number
}

export type CategoryUsers = {
  phrase: string
  all_time: number
  last_30_days: number
}

export type PartnerStats = {
  partner_id: string
  all_time: PeriodStats
  last_30_days: PeriodStats
  category_users: CategoryUsers
}

export const partnerApi = {
  async me(): Promise<PartnerMe> {
    const response = await apiFetch('/api/partner/me')
    if (!response.ok) {
      throw new Error('Не удалось загрузить профиль')
    }
    return (await response.json()) as PartnerMe
  },

  async stats(partnerId: string): Promise<PartnerStats> {
    const response = await apiFetch(`/api/partner/stats?partner_id=${encodeURIComponent(partnerId)}`)
    if (!response.ok) {
      throw new Error('Не удалось загрузить статистику')
    }
    return (await response.json()) as PartnerStats
  },
}
