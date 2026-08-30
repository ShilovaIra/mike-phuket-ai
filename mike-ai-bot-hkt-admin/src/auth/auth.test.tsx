import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { authApi } from './authApi'

test('admin can log in with demo credentials and leaves the login page', async () => {
  const user = userEvent.setup()
  render(
    <MemoryRouter initialEntries={['/login']}>
      <App />
    </MemoryRouter>,
  )

  await user.type(screen.getByLabelText(/email|эл\.?\s*почта|логин/i), 'admin@example.com')
  await user.type(screen.getByLabelText(/пароль/i), 'admin123')
  await user.click(screen.getByRole('button', { name: /войти/i }))

  expect(screen.queryByRole('button', { name: /войти/i })).not.toBeInTheDocument()
  expect(await screen.findByRole('heading', { name: /статистика/i })).toBeInTheDocument()
})

test('unauthenticated visit to /stats redirects to login', () => {
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  expect(screen.getByRole('button', { name: /войти/i })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: /статистика/i })).not.toBeInTheDocument()
})

test('invalid credentials stay on login with an error', async () => {
  const user = userEvent.setup()
  render(
    <MemoryRouter initialEntries={['/login']}>
      <App />
    </MemoryRouter>,
  )

  await user.type(screen.getByLabelText(/email|эл\.?\s*почта|логин/i), 'wrong@mike.local')
  await user.type(screen.getByLabelText(/пароль/i), 'bad')
  await user.click(screen.getByRole('button', { name: /войти/i }))

  expect(await screen.findByRole('alert')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /войти/i })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: /статистика/i })).not.toBeInTheDocument()
})

test('logout clears session and protected routes redirect to login', async () => {
  const user = userEvent.setup()
  render(
    <MemoryRouter initialEntries={['/login']}>
      <App />
    </MemoryRouter>,
  )

  await user.type(screen.getByLabelText(/email|эл\.?\s*почта|логин/i), 'admin@example.com')
  await user.type(screen.getByLabelText(/пароль/i), 'admin123')
  await user.click(screen.getByRole('button', { name: /войти/i }))
  expect(await screen.findByRole('heading', { name: /статистика/i })).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: /выйти/i }))

  expect(await screen.findByRole('button', { name: /войти/i })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: /статистика/i })).not.toBeInTheDocument()
})

test('authenticated visit to /login redirects to stats', async () => {
  await authApi.login({ email: 'admin@example.com', password: 'admin123' })

  render(
    <MemoryRouter initialEntries={['/login']}>
      <App />
    </MemoryRouter>,
  )

  expect(screen.getByRole('heading', { name: /статистика/i })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /войти/i })).not.toBeInTheDocument()
})

test('authenticated shell shows sidebar nav without partner types link', async () => {
  await authApi.login({ email: 'admin@example.com', password: 'admin123' })

  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  const nav = await screen.findByRole('navigation')
  expect(nav.className).toMatch(/flex-col/)
  expect(within(nav).getByRole('link', { name: /статистика/i })).toBeInTheDocument()
  expect(within(nav).getByRole('link', { name: /партнёры/i })).toBeInTheDocument()
  expect(within(nav).getByRole('link', { name: /пользователи партнёров/i })).toBeInTheDocument()
  expect(within(nav).queryByRole('link', { name: /типы партнёров/i })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: /выйти/i })).toBeInTheDocument()
})
