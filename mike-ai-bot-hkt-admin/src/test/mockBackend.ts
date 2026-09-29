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
  logo_url: string
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
  {
    slug: 'esim',
    is_menu_visible: true,
    sort_order: 40,
    button_label: '📱 \neSIM',
    topic_label: '📱 eSIM',
    intro:
      'Чтобы в любой стране оставаться на связи, можно приобрести eSIM в этом боте:',
    fallback:
      'Пока нет доступного бота для покупки eSIM. Напишите Майку — подскажу, что можно сделать.',
    caption_emoji: '📱',
    caption_cta: '⬇️ Купить eSIM ⬇️',
    button_template: 'Купить eSIM',
  },
]

type PlaceCategory = {
  id: string
  slug: string
  label: string
  sort_order: number
}

const seedPlaceCategories: PlaceCategory[] = [
  { id: 'cat-cafe', slug: 'cafe', label: 'Кафе', sort_order: 10 },
  { id: 'cat-restaurant', slug: 'restaurant', label: 'Ресторан', sort_order: 20 },
  { id: 'cat-bar', slug: 'bar', label: 'Бар', sort_order: 30 },
  { id: 'cat-beach', slug: 'beach', label: 'Пляж', sort_order: 40 },
  { id: 'cat-shop', slug: 'shop', label: 'Магазин', sort_order: 50 },
]

const seedPartners: Partner[] = [
  {
    id: '00000000-0000-4000-8000-000000000001',
    name: 'Money Shop',
    type: 'money_exchange',
    referral_url: 'https://moneyshopphuket.online/links/pp413',
    blurb: 'Money Shop',
    logo_path: '',
    logo_url: '',
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
    logo_url: '',
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
    logo_url: '',
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
    logo_url: '',
    is_active: true,
    sort_order: 1,
  },
  {
    id: '00000000-0000-4000-8000-000000000005',
    name: 'Mike eSIM',
    type: 'esim',
    referral_url: 'https://t.me/Mike_esim_bot',
    blurb: '',
    logo_path: 'media/partners/esim.jpeg',
    logo_url: '',
    is_active: true,
    sort_order: 1,
  },
]

let types = structuredClone(seedTypes)
let placeCategories = structuredClone(seedPlaceCategories)
let places: {
  id: string
  name: string
  category: string
  blurb: string
  maps_url: string
  partner_id: string | null
  is_active: boolean
  latitude: number
  longitude: number
  photos: { id: string; path: string }[]
  cover: string
}[] = []
let partners = structuredClone(seedPartners)
let partnerUsers: { id: string; email: string; partners: { id: string; name: string }[] }[] = []
let partnerTypesListFailure: { status: number; detail: string } | null = null
let logoUploads = new Map<string, string>()
let logoStorageDown = false
let logoLinkDown = false

export const MOCK_CDN = 'https://cdn-test.mikephuketai.com'
const STORAGE_DOWN = 'Хранилище недоступно, попробуйте позже'
const MAX_LOGO_BYTES = 5 * 1024 * 1024

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export function resetMockBackend(): void {
  types = structuredClone(seedTypes)
  placeCategories = structuredClone(seedPlaceCategories)
  places = []
  partners = structuredClone(seedPartners)
  partnerUsers = []
  partnerTypesListFailure = null
  logoUploads = new Map()
  logoStorageDown = false
  logoLinkDown = false
}

export function failLogoStorage(): void {
  logoStorageDown = true
}

export function failLogoLink(): void {
  logoLinkDown = true
}

export function restoreLogoLink(): void {
  logoLinkDown = false
}

export function mockPartnerByName(name: string): Partner | undefined {
  return partners.find((p) => p.name === name)
}

async function sniffLogo(file: File): Promise<string | null> {
  const head = new Uint8Array(await file.slice(0, 8).arrayBuffer())
  if (head[0] === 0x89 && head[1] === 0x50 && head[2] === 0x4e && head[3] === 0x47) return 'png'
  if (head[0] === 0xff && head[1] === 0xd8 && head[2] === 0xff) return 'jpg'
  return null
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
    const body =
      init?.body && !(init.body instanceof FormData) ? JSON.parse(String(init.body)) : null

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

    if (path === '/api/place-categories' && method === 'GET') {
      return json([...placeCategories].sort((a, b) => a.sort_order - b.sort_order))
    }

    if (path === '/api/place-categories' && method === 'POST') {
      const category = { id: crypto.randomUUID(), ...body }
      placeCategories.push(category)
      return json(category, 201)
    }

    const placeCategoryMatch = path.match(/^\/api\/place-categories\/([^/]+)$/)
    if (placeCategoryMatch && method === 'PATCH') {
      const slug = decodeURIComponent(placeCategoryMatch[1])
      const index = placeCategories.findIndex((category) => category.slug === slug)
      if (index < 0) return json({ detail: 'not found' }, 404)
      placeCategories[index] = {
        ...placeCategories[index],
        label: body.label,
        sort_order: body.sort_order,
      }
      return json(placeCategories[index])
    }

    if (placeCategoryMatch && method === 'DELETE') {
      const slug = decodeURIComponent(placeCategoryMatch[1])
      const used = places.some((place) => place.category === slug)
      if (used) return json({ detail: 'Категорию используют места' }, 409)
      placeCategories = placeCategories.filter((category) => category.slug !== slug)
      return new Response(null, { status: 204 })
    }

    if (path === '/api/places' && method === 'GET') {
      return json([...places])
    }

    if (path === '/api/places' && method === 'POST') {
      const place = {
        id: crypto.randomUUID(),
        name: body.name as string,
        category: body.category as string,
        blurb: (body.blurb as string) ?? '',
        maps_url: body.maps_url as string,
        partner_id: (body.partner_id as string | null) ?? null,
        is_active: body.is_active !== false,
        latitude: 7.76,
        longitude: 98.3,
        photos: [],
        cover: 'media/places/placeholder.jpg',
      }
      places.push(place)
      return json(place, 201)
    }

    if (path === '/api/partners' && method === 'GET') {
      return json([...partners])
    }

    if (path === '/api/partners' && method === 'POST') {
      const partner = {
        id: crypto.randomUUID(),
        ...body,
        logo_path: '',
        logo_url: '',
      }
      partners.push(partner)
      return json(partner, 201)
    }

    const partnerMatch = path.match(/^\/api\/partners\/([^/]+)$/)
    if (partnerMatch && method === 'PATCH') {
      const id = decodeURIComponent(partnerMatch[1])
      const index = partners.findIndex((p) => p.id === id)
      if (index < 0) return json({ detail: 'not found' }, 404)
      partners[index] = {
        ...partners[index],
        ...body,
        logo_path: partners[index].logo_path,
        logo_url: partners[index].logo_url,
      }
      return json(partners[index])
    }

    if (path === '/api/partner-logos/uploads' && method === 'POST') {
      const file = (init!.body as FormData).get('file') as File
      if (file.size > MAX_LOGO_BYTES) return json({ detail: 'Файл больше 5 МБ' }, 400)
      const extension = await sniffLogo(file)
      if (!extension) return json({ detail: 'Только JPEG или PNG' }, 400)
      if (logoStorageDown) return json({ detail: STORAGE_DOWN }, 503)
      const token = `upload-${crypto.randomUUID()}`
      const previewUrl = `${MOCK_CDN}/tmp/${token}.${extension}`
      logoUploads.set(token, extension)
      return json({ upload_token: token, preview_url: previewUrl }, 201)
    }

    const logoMatch = path.match(/^\/api\/partners\/([^/]+)\/logo$/)
    if (logoMatch && (method === 'PUT' || method === 'DELETE')) {
      const id = decodeURIComponent(logoMatch[1])
      const index = partners.findIndex((p) => p.id === id)
      if (index < 0) return json({ detail: 'Партнёр не найден' }, 404)
      if (method === 'DELETE') {
        partners[index] = { ...partners[index], logo_path: '', logo_url: '' }
        return json(partners[index])
      }
      if (logoLinkDown) return json({ detail: STORAGE_DOWN }, 503)
      const extension = logoUploads.get(body.upload_token)
      if (!extension) return json({ detail: 'Загрузка устарела, выберите файл заново' }, 400)
      const key = `partners/${id}/logo-${body.upload_token.slice(-12)}.${extension}`
      partners[index] = { ...partners[index], logo_path: key, logo_url: `${MOCK_CDN}/${key}` }
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
