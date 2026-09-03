type PartnerType = {
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

type Partner = {
  id: string
  name: string
  type: string
  referral_url: string
  blurb: string
  logo_path: string
  is_active: boolean
  sort_order: number
}

const seedTypes: PartnerType[] = [
  {
    slug: 'money_exchange',
    is_menu_visible: true,
    sort_order: 10,
    button_label: '💰 \nОбмен Рублей',
    topic_label: '💰 Обмен',
    intro: 'Вот партнёры для обмена рублей:',
    fallback: 'Пока нет доступных партнёров по обмену.',
    caption_emoji: '💰',
    caption_cta: '⬇️ Обменять сейчас ⬇️',
    button_template: 'Обменять с {name}',
  },
  {
    slug: 'vehicle_rental',
    is_menu_visible: true,
    sort_order: 20,
    button_label: '🛵 \nАренда транспорта',
    topic_label: '🛵 Аренда транспорта',
    intro: 'Вот партнёры по аренде транспорта:',
    fallback: 'Пока нет доступных партнёров по аренде транспорта.',
    caption_emoji: '🛵',
    caption_cta: '⬇️ Арендовать сейчас ⬇️',
    button_template: 'Арендовать у {name}',
  },
  {
    slug: 'excursions',
    is_menu_visible: true,
    sort_order: 30,
    button_label: '🇹🇭 \nЭкскурсии',
    topic_label: '🇹🇭 Экскурсии',
    intro: 'Вот партнёры по экскурсиям:',
    fallback: 'Пока нет доступных партнёров по экскурсиям.',
    caption_emoji: '🇹🇭',
    caption_cta: '⬇️ Забронировать сейчас ⬇️',
    button_template: 'Забронировать с {name}',
  },
]

const seedPartners: Partner[] = [
  {
    id: '00000000-0000-4000-8000-000000000001',
    name: 'Money Shop',
    type: 'money_exchange',
    referral_url: 'https://moneyshopphuket.online/links/pp413',
    blurb: 'Money Shop',
    logo_path: '',
    is_active: true,
    sort_order: 1,
  },
  {
    id: '00000000-0000-4000-8000-000000000002',
    name: 'Ex24.pro',
    type: 'money_exchange',
    referral_url: 'https://ex24qr.com/epihelgnld',
    blurb: 'Ex24',
    logo_path: '',
    is_active: true,
    sort_order: 2,
  },
  {
    id: '00000000-0000-4000-8000-000000000003',
    name: 'Остров Сокровищ',
    type: 'excursions',
    referral_url: 'https://tisland.link/excurs?ref=72s5z3yp3jb79r7',
    blurb: 'Экскурсии',
    logo_path: '',
    is_active: true,
    sort_order: 1,
  },
  {
    id: '00000000-0000-4000-8000-000000000004',
    name: 'Boomerang',
    type: 'vehicle_rental',
    referral_url: 'https://boomerang.rent/catalog/?utm_source=MikePhuketAIBot',
    blurb: 'Boomerang - надежный сервис аренды автомобилей и мотобайков на Пхукете. Доставка по всему острову.',
    logo_path: 'media/partners/boomerang.jpeg',
    is_active: true,
    sort_order: 1,
  },
]

let types = structuredClone(seedTypes)
let partners = structuredClone(seedPartners)
let partnerUsers: { id: string; email: string; partners: { id: string; name: string }[] }[] = []
let partnerTypesListFailure: { status: number; detail: string } | null = null

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export function resetMockBackend(): void {
  types = structuredClone(seedTypes)
  partners = structuredClone(seedPartners)
  partnerUsers = []
  partnerTypesListFailure = null
}

export function failPartnerTypesList(status: number, detail: string): void {
  partnerTypesListFailure = { status, detail }
}

export function installFetchMock(): void {
  resetMockBackend()
  vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost:8000')
    const path = url.pathname
    const method = (init?.method ?? 'GET').toUpperCase()
    const body = init?.body ? JSON.parse(String(init.body)) : null

    if (path === '/api/auth/login' && method === 'POST') {
      if (body?.email === 'admin@example.com' && body?.password === 'admin123') {
        return json({ access_token: 'test-token', token_type: 'bearer' })
      }
      return json({ detail: 'Неверный email или пароль' }, 401)
    }

    const auth = new Headers(init?.headers).get('Authorization')
    if (path === '/api/auth/me' && method === 'GET') {
      if (auth !== 'Bearer test-token') return json({ detail: 'Invalid token' }, 401)
      return json({ email: 'admin@example.com' })
    }

    if (path === '/api/stats' && method === 'GET') {
      return json({
        total_users: 128,
        new_users_today: 4,
        active_today: 17,
        new_users_7d: 22,
        topics_all_time: [
          { slug: 'beaches', label: '🏖 Пляжи', unique_users: 40, taps: 55 },
          { slug: 'ask_mike', label: '💬 Спросить Майка', unique_users: 36, taps: 80 },
          { slug: 'money_exchange', label: '💰 Обмен', unique_users: 28, taps: 33 },
        ],
        topics_7d: [
          { slug: 'beaches', label: '🏖 Пляжи', unique_users: 12, taps: 15 },
          { slug: 'ask_mike', label: '💬 Спросить Майка', unique_users: 10, taps: 18 },
          { slug: 'money_exchange', label: '💰 Обмен', unique_users: 8, taps: 9 },
        ],
        leads_all_time: 9,
        leads_7d: 2,
        users_by_first_source: { unknown: 90, instagram: 25, facebook: 13 },
      })
    }

    if (path === '/api/partner-types' && method === 'GET') {
      if (partnerTypesListFailure) {
        return json({ detail: partnerTypesListFailure.detail }, partnerTypesListFailure.status)
      }
      return json([...types].sort((a, b) => a.sort_order - b.sort_order))
    }

    if (path === '/api/partner-types' && method === 'POST') {
      types.push(body)
      return json(body, 201)
    }

    const typeMatch = path.match(/^\/api\/partner-types\/([^/]+)$/)
    if (typeMatch && method === 'PATCH') {
      const slug = decodeURIComponent(typeMatch[1])
      const index = types.findIndex((t) => t.slug === slug)
      if (index < 0) return json({ detail: 'not found' }, 404)
      if (body.slug !== slug) {
        partners = partners.map((p) => (p.type === slug ? { ...p, type: body.slug } : p))
      }
      types[index] = body
      return json(body)
    }

    if (path === '/api/partners' && method === 'GET') {
      return json([...partners])
    }

    if (path === '/api/partners' && method === 'POST') {
      const partner = {
        id: crypto.randomUUID(),
        ...body,
        logo_path: '',
      }
      partners.push(partner)
      return json(partner, 201)
    }

    const partnerMatch = path.match(/^\/api\/partners\/([^/]+)$/)
    if (partnerMatch && method === 'PATCH') {
      const id = decodeURIComponent(partnerMatch[1])
      const index = partners.findIndex((p) => p.id === id)
      if (index < 0) return json({ detail: 'not found' }, 404)
      partners[index] = { ...partners[index], ...body, logo_path: '' }
      return json(partners[index])
    }

    if (path === '/api/partner-users' && method === 'GET') {
      return json([...partnerUsers])
    }

    if (path === '/api/partner-users' && method === 'POST') {
      const selected = partners.filter((p) => (body.partner_ids as string[]).includes(p.id))
      const row = {
        id: crypto.randomUUID(),
        email: body.email as string,
        partners: selected.map((p) => ({ id: p.id, name: p.name })),
      }
      partnerUsers.push(row)
      return json(row, 201)
    }

    const partnerUserMatch = path.match(/^\/api\/partner-users\/([^/]+)$/)
    if (partnerUserMatch && method === 'DELETE') {
      const id = decodeURIComponent(partnerUserMatch[1])
      partnerUsers = partnerUsers.filter((u) => u.id !== id)
      return new Response(null, { status: 204 })
    }

    return json({ detail: `unmocked ${method} ${path}` }, 404)
  })
}
