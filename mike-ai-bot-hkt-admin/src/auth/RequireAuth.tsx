import { useEffect, useState } from 'react'
import { NavLink, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { apiFetch, authApi, SESSION_EVENT } from './authApi'
import { Icon } from '../shell/icons'

const LINKS = [
  { to: '/stats', label: 'Статистика', icon: 'chart' },
  { to: '/broadcasts', label: 'Рассылка', icon: 'send' },
  { to: '/partners', label: 'Партнёры', icon: 'users' },
  { to: '/partner-types', label: 'Типы партнёров', icon: 'tag' },
  { to: '/places', label: 'Места', icon: 'pin' },
  { to: '/knowledge-base', label: 'База знаний', icon: 'book' },
  { to: '/place-categories', label: 'Категории мест', icon: 'layers' },
  { to: '/partner-users', label: 'Пользователи партнёров', icon: 'idcard' },
] as const

export function RequireAuth() {
  const navigate = useNavigate()
  const location = useLocation()
  const [session, setSession] = useState(() => authApi.getSession())
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const sync = () => setSession(authApi.getSession())
    window.addEventListener(SESSION_EVENT, sync)
    return () => window.removeEventListener(SESSION_EVENT, sync)
  }, [])

  useEffect(() => {
    if (!session) return
    void apiFetch('/api/auth/me')
  }, [session])

  useEffect(() => {
    setOpen(false)
  }, [location.pathname])

  if (!session) {
    return <Navigate to="/login" replace />
  }

  function logout() {
    authApi.logout()
    navigate('/login', { replace: true })
  }

  const name = session.email.split('@')[0] || session.email

  return (
    <div className="desk">
      <button
        type="button"
        className={open ? 'desk-backdrop is-open' : 'desk-backdrop'}
        aria-label="Закрыть меню"
        onClick={() => setOpen(false)}
      />
      <aside className={open ? 'desk-rail is-open' : 'desk-rail'}>
        <div className="desk-brand">
          <span className="desk-mark">
            <Icon name="spark" />
          </span>
          Admin Panel
        </div>
        <nav className="desk-nav flex-col" aria-label="Разделы">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => `desk-link${isActive ? ' is-active' : ''}`}
            >
              <Icon name={link.icon} />
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="desk-user">
          <span className="desk-avatar" aria-hidden="true">
            {name.slice(0, 1).toUpperCase()}
          </span>
          <p title={session.email}>{name}</p>
          <button type="button" className="desk-logout" onClick={logout}>
            Выйти
          </button>
        </div>
      </aside>
      <div className="desk-main">
        <div className="desk-stage">
          <button type="button" className="ghost-button desk-menu" onClick={() => setOpen(true)}>
            Меню
          </button>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
