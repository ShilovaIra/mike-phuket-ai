import { useEffect, useState } from 'react'
import { Link, Navigate, Outlet, useNavigate } from 'react-router-dom'
import { apiFetch, authApi, SESSION_EVENT } from './authApi'

export function RequireAuth() {
  const navigate = useNavigate()
  const [session, setSession] = useState(() => authApi.getSession())

  useEffect(() => {
    const sync = () => setSession(authApi.getSession())
    window.addEventListener(SESSION_EVENT, sync)
    return () => window.removeEventListener(SESSION_EVENT, sync)
  }, [])

  useEffect(() => {
    if (!session) return
    void apiFetch('/api/auth/me')
  }, [session])

  if (!session) {
    return <Navigate to="/login" replace />
  }

  function logout() {
    authApi.logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-52 shrink-0 flex-col border-r border-slate-200 bg-white px-3 py-4">
        <nav className="flex flex-col gap-1 text-sm">
          <Link to="/stats" className="rounded px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-slate-900">
            Статистика
          </Link>
          <Link
            to="/partners"
            className="rounded px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-slate-900"
          >
            Партнёры
          </Link>
          <Link
            to="/partner-types"
            className="rounded px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-slate-900"
          >
            Типы партнёров
          </Link>
          <Link
            to="/places"
            className="rounded px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-slate-900"
          >
            Места
          </Link>
          <Link
            to="/knowledge-base"
            className="rounded px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-slate-900"
          >
            База знаний
          </Link>
          <Link
            to="/place-categories"
            className="rounded px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-slate-900"
          >
            Категории мест
          </Link>
          <Link
            to="/partner-users"
            className="rounded px-3 py-2 text-slate-700 hover:bg-slate-50 hover:text-slate-900"
          >
            Пользователи партнёров
          </Link>
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-end border-b border-slate-200 bg-white px-4 py-3">
          <button
            type="button"
            onClick={logout}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
          >
            Выйти
          </button>
        </header>
        <Outlet />
      </div>
    </div>
  )
}
