import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import logo from '../assets/logo/mike-phuket-ai.png'
import { authApi } from './authApi'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  if (authApi.getSession()) {
    return <Navigate to="/stats" replace />
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setError(null)
    const result = await authApi.login({ email, password })
    setPending(false)
    if (!result.ok) {
      setError(result.error)
      return
    }
    navigate('/stats', { replace: true })
  }

  return (
    <main className="login-scene">
      <div className="glass-pane login-card">
        <img src={logo} alt="Mike Phuket AI" width={480} height={240} className="login-logo" />
        <h1>Вход</h1>
        <form onSubmit={onSubmit}>
          <label className="cast-label">
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="glass-field"
              autoComplete="username"
              required
            />
          </label>
          <label className="cast-label">
            Пароль
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="glass-field"
              autoComplete="current-password"
              required
            />
          </label>
          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
          <button type="submit" disabled={pending} className="ice-button">
            Войти
          </button>
        </form>
      </div>
    </main>
  )
}
