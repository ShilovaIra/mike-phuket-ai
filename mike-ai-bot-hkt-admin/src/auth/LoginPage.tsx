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
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      <img src={logo} alt="Mike Phuket AI" width={240} height={120} className="mb-6 h-auto w-[240px] self-center" />
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Вход</h1>
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded border border-slate-300 bg-white px-3 py-2"
            autoComplete="username"
            required
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Пароль
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded border border-slate-300 bg-white px-3 py-2"
            autoComplete="current-password"
            required
          />
        </label>
        {error ? <p role="alert">{error}</p> : null}
        <button
          type="submit"
          disabled={pending}
          className="rounded bg-[#053e7a] px-4 py-2 text-white hover:bg-[#042f5c] disabled:opacity-60"
        >
          Войти
        </button>
      </form>
    </main>
  )
}
