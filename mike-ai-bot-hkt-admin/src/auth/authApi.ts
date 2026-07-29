const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type AdminSession = {
  email: string
  accessToken: string
}

const SESSION_KEY = 'mike-ai-admin-session'

export type LoginCredentials = {
  email: string
  password: string
}

export type LoginResult =
  | { ok: true; session: AdminSession }
  | { ok: false; error: string }

export function getAccessToken(): string | null {
  return authApi.getSession()?.accessToken ?? null
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }
  const token = getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return fetch(`${API_BASE}${path}`, { ...init, headers })
}

export const authApi = {
  getSession(): AdminSession | null {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as AdminSession
    } catch {
      return null
    }
  },

  async login({ email, password }: LoginCredentials): Promise<LoginResult> {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!response.ok) {
      return { ok: false, error: 'Неверный email или пароль' }
    }
    const body = (await response.json()) as { access_token: string }
    const session: AdminSession = { email, accessToken: body.access_token }
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    return { ok: true, session }
  },

  logout(): void {
    localStorage.removeItem(SESSION_KEY)
  },
}
