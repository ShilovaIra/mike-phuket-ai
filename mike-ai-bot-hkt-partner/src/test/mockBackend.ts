type PeriodStats = {
  views: number
  referral_clicks: number
  opened_views: number
}

const MONEY_SHOP = {
  id: '00000000-0000-4000-8000-000000000001',
  name: 'Money Shop',
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export function resetMockBackend(): void {}

export function installFetchMock(): void {
  vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost:8000')
    const path = url.pathname
    const method = (init?.method ?? 'GET').toUpperCase()
    const body = init?.body ? JSON.parse(String(init.body)) : null

    if (path === '/api/partner/auth/login' && method === 'POST') {
      if (body?.email === 'shop@example.com' && body?.password === 'shop-secret') {
        return json({ access_token: 'partner-token', token_type: 'bearer' })
      }
      return json({ detail: 'Неверный email или пароль' }, 401)
    }

    const auth = new Headers(init?.headers).get('Authorization')
    if (auth !== 'Bearer partner-token') {
      return json({ detail: 'Not authenticated' }, 401)
    }

    if (path === '/api/partner/me' && method === 'GET') {
      return json({ email: 'shop@example.com', partners: [MONEY_SHOP] })
    }

    if (path === '/api/partner/stats' && method === 'GET') {
      return json({
        partner_id: MONEY_SHOP.id,
        all_time: { views: 10, referral_clicks: 4, opened_views: 3 } satisfies PeriodStats,
        last_30_days: { views: 5, referral_clicks: 2, opened_views: 1 },
        category_users: { phrase: 'обмен рублей', all_time: 42, last_30_days: 7 },
      })
    }

    return json({ detail: `unmocked ${method} ${path}` }, 404)
  })
}
