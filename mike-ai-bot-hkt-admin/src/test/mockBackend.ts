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
  choice_phrase: string
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
    choice_phrase: 'обмен рублей',
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
    choice_phrase: 'аренду транспорта',
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
    choice_phrase: 'экскурсии',
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
    choice_phrase: 'eSIM',
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
  mike_recommends: boolean
  latitude: number
  longitude: number
  photos: { id: string; path: string; url: string }[]
  cover: string
}[] = []

function seedPlaces() {
  return [
    {
      id: 'place-treasure',
      name: 'Офис Острова',
      category: 'shop',
      blurb: '',
      maps_url: 'https://maps.example/treasure',
      partner_id: '00000000-0000-4000-8000-000000000003',
      is_active: true,
      mike_recommends: false,
      latitude: 7.8,
      longitude: 98.3,
      photos: [],
      cover: 'media/places/placeholder.jpg',
    },
  ]
}

let partners = structuredClone(seedPartners)

type KnowledgeBaseRow = {
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

function seedKnowledgeBase(): KnowledgeBaseRow[] {
  return [
    {
      id: 'kb-money-shop',
      partner_id: '00000000-0000-4000-8000-000000000001',
      place_id: null,
      name: 'Money Shop',
      kind: '💰 Обмен',
      blurb: 'Money Shop',
      referral_url: 'https://moneyshopphuket.online/links/pp413',
      maps_url: '',
      in_chat: true,
    },
    {
      id: 'kb-ex24',
      partner_id: '00000000-0000-4000-8000-000000000002',
      place_id: null,
      name: 'Ex24.pro',
      kind: '💰 Обмен',
      blurb: 'Ex24',
      referral_url: 'https://ex24qr.com/epihelgnld',
      maps_url: '',
      in_chat: false,
    },
    {
      id: 'kb-pier',
      partner_id: null,
      place_id: 'place-pier',
      name: 'Reef Divers Pier',
      kind: 'Магазин',
      blurb: '',
      referral_url: 'https://example.com/reef',
      maps_url: 'https://maps.example/reef',
      in_chat: true,
    },
    {
      id: 'kb-treasure',
      partner_id: null,
      place_id: 'place-treasure',
      name: 'Офис Острова',
      kind: 'Магазин',
      blurb: '',
      referral_url: 'https://tisland.link/excurs?ref=72s5z3yp3jb79r7',
      maps_url: 'https://maps.example/treasure',
      in_chat: true,
    },
  ]
}

let knowledgeBase: KnowledgeBaseRow[] = seedKnowledgeBase()
let broadcasts: {
  id: string
  text: string
  scheduled_at: string
  status: 'scheduled' | 'sent'
  button_url: string | null
  button_label: string | null
}[] = []
let broadcastLists: {
  id: string
  name: string
  messages: {
    id: string
    text: string
    button_url: string | null
    button_label: string | null
  }[]
}[] = []
let intervalBroadcasts: {
  id: string
  list_id: string
  list_name: string
  interval_days: number
  scheduled_at: string
  next_message: {
    id: string
    text: string
    button_url: string | null
    button_label: string | null
  } | null
}[] = []
let partnerUsers: { id: string; email: string; partners: { id: string; name: string }[] }[] = []
let partnerTypesListFailure: { status: number; detail: string } | null = null
let logoUploads = new Map<string, string>()
let photoUploads = new Map<string, string>()
let placePhotoSaveDown = false
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
  places = seedPlaces()
  partners = structuredClone(seedPartners)
  knowledgeBase = seedKnowledgeBase()
  broadcasts = []
  broadcastLists = []
  intervalBroadcasts = []
  partnerUsers = []
  partnerTypesListFailure = null
  logoUploads = new Map()
  photoUploads = new Map()
  placePhotoSaveDown = false
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

export function failPlacePhotoSave(): void {
  placePhotoSaveDown = true
}

export function restorePlacePhotoSave(): void {
  placePhotoSaveDown = false
}

export function seedBroadcastLists(
  items: {
    id: string
    name: string
    messages: {
      id: string
      text: string
      button_url: string | null
      button_label: string | null
    }[]
  }[],
): void {
  broadcastLists = items
}

export function seedIntervalBroadcasts(
  items: {
    id: string
    list_id: string
    list_name: string
    interval_days: number
    scheduled_at: string
    next_message: {
      id: string
      text: string
      button_url: string | null
      button_label: string | null
    } | null
  }[],
): void {
  intervalBroadcasts = items
}

export function seedBroadcasts(
  items: {
    id: string
    text: string
    scheduled_at: string
    status: 'scheduled' | 'sent'
    button_url: string | null
    button_label: string | null
  }[],
): void {
  broadcasts = items
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

    if (path === '/api/broadcasts' && method === 'GET') {
      return json(broadcasts)
    }

    if (path === '/api/broadcasts' && method === 'POST') {
      const created = {
        id: crypto.randomUUID(),
        text: String(body.text).trim(),
        scheduled_at: body.scheduled_at as string,
        status: 'scheduled' as const,
        button_url: (body.button_url as string | null) || null,
        button_label: (body.button_label as string | null) || null,
      }
      broadcasts.push(created)
      return json(created, 201)
    }

    const broadcastMatch = path.match(/^\/api\/broadcasts\/([^/]+)$/)
    if (broadcastMatch && method === 'PATCH') {
      const id = decodeURIComponent(broadcastMatch[1])
      const index = broadcasts.findIndex((item) => item.id === id)
      if (index < 0) return json({ detail: 'not found' }, 404)
      broadcasts[index] = {
        ...broadcasts[index],
        text: String(body.text).trim(),
        scheduled_at: body.scheduled_at as string,
        button_url: (body.button_url as string | null) || null,
        button_label: (body.button_label as string | null) || null,
      }
      return json(broadcasts[index])
    }

    if (broadcastMatch && method === 'DELETE') {
      const id = decodeURIComponent(broadcastMatch[1])
      broadcasts = broadcasts.filter((item) => item.id !== id)
      return new Response(null, { status: 204 })
    }

    if (path === '/api/broadcast-lists' && method === 'GET') {
      return json(broadcastLists)
    }

    if (path === '/api/broadcast-lists' && method === 'POST') {
      const created = {
        id: crypto.randomUUID(),
        name: String(body.name).trim(),
        messages: [] as (typeof broadcastLists)[number]['messages'],
      }
      broadcastLists.push(created)
      return json(created, 201)
    }

    const listMatch = path.match(/^\/api\/broadcast-lists\/([^/]+)$/)
    if (listMatch && method === 'DELETE') {
      const id = decodeURIComponent(listMatch[1])
      if (intervalBroadcasts.some((item) => item.list_id === id)) {
        return json({ detail: 'Список используют рассылки' }, 409)
      }
      const exists = broadcastLists.some((item) => item.id === id)
      if (!exists) return json({ detail: 'not found' }, 404)
      broadcastLists = broadcastLists.filter((item) => item.id !== id)
      return new Response(null, { status: 204 })
    }

    const listMessageMatch = path.match(/^\/api\/broadcast-lists\/([^/]+)\/messages$/)
    if (listMessageMatch && method === 'POST') {
      const listId = decodeURIComponent(listMessageMatch[1])
      const list = broadcastLists.find((item) => item.id === listId)
      if (!list) return json({ detail: 'not found' }, 404)
      const created = {
        id: crypto.randomUUID(),
        text: String(body.text).trim(),
        button_url: (body.button_url as string | null) || null,
        button_label: (body.button_label as string | null) || null,
      }
      list.messages.push(created)
      return json(created, 201)
    }

    const moveMatch = path.match(/^\/api\/broadcast-lists\/([^/]+)\/messages\/([^/]+)\/move$/)
    if (moveMatch && method === 'POST') {
      const listId = decodeURIComponent(moveMatch[1])
      const messageId = decodeURIComponent(moveMatch[2])
      const list = broadcastLists.find((item) => item.id === listId)
      if (!list) return json({ detail: 'not found' }, 404)
      const index = list.messages.findIndex((item) => item.id === messageId)
      if (index < 0) return json({ detail: 'not found' }, 404)
      const swapWith = body.direction === 'up' ? index - 1 : index + 1
      if (swapWith >= 0 && swapWith < list.messages.length) {
        const current = list.messages[index]
        list.messages[index] = list.messages[swapWith]
        list.messages[swapWith] = current
      }
      return json({ ok: true })
    }

    if (path === '/api/interval-broadcasts' && method === 'GET') {
      return json(intervalBroadcasts)
    }

    if (path === '/api/interval-broadcasts' && method === 'POST') {
      const list = broadcastLists.find((item) => item.id === body.list_id)
      if (!list) return json({ detail: 'not found' }, 404)
      const created = {
        id: crypto.randomUUID(),
        list_id: list.id,
        list_name: list.name,
        interval_days: Number(body.interval_days),
        scheduled_at: body.scheduled_at as string,
        next_message: list.messages[0] ?? null,
      }
      intervalBroadcasts.push(created)
      return json(created, 201)
    }

    const intervalMatch = path.match(/^\/api\/interval-broadcasts\/([^/]+)$/)
    if (intervalMatch && method === 'PATCH') {
      const id = decodeURIComponent(intervalMatch[1])
      const index = intervalBroadcasts.findIndex((item) => item.id === id)
      if (index < 0) return json({ detail: 'not found' }, 404)
      intervalBroadcasts[index] = {
        ...intervalBroadcasts[index],
        interval_days:
          body.interval_days == null
            ? intervalBroadcasts[index].interval_days
            : Number(body.interval_days),
        scheduled_at:
          (body.scheduled_at as string | undefined) ?? intervalBroadcasts[index].scheduled_at,
      }
      return json(intervalBroadcasts[index])
    }

    if (intervalMatch && method === 'DELETE') {
      const id = decodeURIComponent(intervalMatch[1])
      intervalBroadcasts = intervalBroadcasts.filter((item) => item.id !== id)
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
        mike_recommends: body.mike_recommends === true,
        latitude: 7.76,
        longitude: 98.3,
        photos: [],
        cover: 'media/places/placeholder.jpg',
      }
      places.push(place)
      return json(place, 201)
    }

    if (path === '/api/place-photos/uploads' && method === 'POST') {
      const file = (init!.body as FormData).get('file') as File
      if (file.size > MAX_LOGO_BYTES) return json({ detail: 'Файл больше 5 МБ' }, 400)
      const extension = await sniffLogo(file)
      if (!extension) return json({ detail: 'Только JPEG или PNG' }, 400)
      const token = `upload-${crypto.randomUUID()}`
      const previewUrl = `${MOCK_CDN}/tmp/${token}.${extension}`
      photoUploads.set(token, extension)
      return json({ upload_token: token, preview_url: previewUrl }, 201)
    }

    const placeMatch = path.match(/^\/api\/places\/([^/]+)$/)
    if (placeMatch && method === 'PATCH') {
      const id = decodeURIComponent(placeMatch[1])
      const index = places.findIndex((place) => place.id === id)
      if (index < 0) return json({ detail: 'Место не найдено' }, 404)
      const current = places[index]
      let photos = current.photos
      if (Array.isArray(body.photos)) {
        if (body.photos.length > 0 && placePhotoSaveDown) {
          return json({ detail: 'Хранилище недоступно, попробуйте позже' }, 503)
        }
        if (body.photos.length === 0) {
          photos = []
        } else {
          const token = body.photos[0].upload_token as string
          const extension = photoUploads.get(token)
          if (!extension) return json({ detail: 'Загрузка устарела, выберите файл заново' }, 400)
          const key = `places/${id}/${token.slice(-12)}.${extension}`
          photos = [{ id: crypto.randomUUID(), path: key, url: `${MOCK_CDN}/${key}` }]
        }
      }
      places[index] = {
        ...current,
        name: body.name ?? current.name,
        category: body.category ?? current.category,
        blurb: body.blurb ?? current.blurb,
        maps_url: body.maps_url ?? current.maps_url,
        partner_id: body.partner_id === undefined ? current.partner_id : body.partner_id,
        is_active: body.is_active ?? current.is_active,
        mike_recommends: body.mike_recommends ?? current.mike_recommends,
        photos,
        cover: photos[0]?.path ?? 'media/places/placeholder.jpg',
      }
      return json(places[index])
    }

    if (path === '/api/knowledge-base' && method === 'GET') {
      return json([...knowledgeBase])
    }

    if (path === '/api/knowledge-base' && method === 'POST' && body?.partner_id) {
      const partner = partners.find((item) => item.id === body.partner_id)
      if (!partner) return json({ detail: 'Партнёр не найден' }, 404)
      if (knowledgeBase.some((row) => row.partner_id === partner.id)) {
        return json({ detail: 'Уже в базе знаний' }, 409)
      }
      const kind = types.find((type) => type.slug === partner.type)?.topic_label ?? ''
      const row = {
        id: crypto.randomUUID(),
        partner_id: partner.id,
        place_id: null,
        name: partner.name,
        kind,
        blurb: partner.blurb,
        referral_url: partner.referral_url,
        maps_url: '',
        in_chat: partner.is_active,
      }
      knowledgeBase.push(row)
      return json(row, 201)
    }

    const knowledgeBaseMatch = path.match(/^\/api\/knowledge-base\/([^/]+)$/)
    if (knowledgeBaseMatch && method === 'DELETE') {
      const id = decodeURIComponent(knowledgeBaseMatch[1])
      knowledgeBase = knowledgeBase.filter((row) => row.id !== id)
      return new Response(null, { status: 204 })
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
