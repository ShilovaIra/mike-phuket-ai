import { Link, Navigate, Outlet, useNavigate } from 'react-router-dom'
import { authApi } from './authApi'

export function RequireAuth() {
  const navigate = useNavigate()

  if (!authApi.getSession()) {
    return <Navigate to="/login" replace />
  }

  function logout() {
    authApi.logout()
    navigate('/login', { replace: true })
  }

  return (
    <>
      <header className="flex items-center justify-between gap-4 border-b border-slate-200 bg-white px-4 py-3">
        <nav className="flex items-center gap-4 text-sm">
          <Link to="/stats" className="text-slate-700 hover:text-slate-900">
            Статистика
          </Link>
          <Link to="/partners" className="text-slate-700 hover:text-slate-900">
            Партнёры
          </Link>
          <Link to="/partner-types" className="text-slate-700 hover:text-slate-900">
            Типы партнёров
          </Link>
        </nav>
        <button
          type="button"
          onClick={logout}
          className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
        >
          Выйти
        </button>
      </header>
      <Outlet />
    </>
  )
}
