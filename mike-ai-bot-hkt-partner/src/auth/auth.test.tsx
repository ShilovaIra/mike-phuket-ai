import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { authApi } from './authApi'

test('partner user can log in and sees stats', async () => {
  const user = userEvent.setup()
  render(
    <MemoryRouter initialEntries={['/login']}>
      <App />
    </MemoryRouter>,
  )

  await user.type(screen.getByLabelText(/email|эл\.?\s*почта|логин/i), 'shop@example.com')
  await user.type(screen.getByLabelText(/пароль/i), 'shop-secret')
  await user.click(screen.getByRole('button', { name: /войти/i }))

  expect(await screen.findByRole('heading', { name: /статистика/i })).toBeInTheDocument()
  expect(await screen.findByText('Показы (всё время)')).toBeInTheDocument()
  expect(screen.getByText('10')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /показы: переход или нет/i })).toBeInTheDocument()
  expect(screen.queryByLabelText(/^партнёр$/i)).not.toBeInTheDocument()
})

test('unauthenticated visit to /stats redirects to login', () => {
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  expect(screen.getByRole('button', { name: /войти/i })).toBeInTheDocument()
})

test('invalid credentials stay on login with an error', async () => {
  const user = userEvent.setup()
  render(
    <MemoryRouter initialEntries={['/login']}>
      <App />
    </MemoryRouter>,
  )

  await user.type(screen.getByLabelText(/email|эл\.?\s*почта|логин/i), 'wrong@example.com')
  await user.type(screen.getByLabelText(/пароль/i), 'bad')
  await user.click(screen.getByRole('button', { name: /войти/i }))

  expect(await screen.findByRole('alert')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /войти/i })).toBeInTheDocument()
})

test('logout returns to login', async () => {
  await authApi.login({ email: 'shop@example.com', password: 'shop-secret' })
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )
  expect(await screen.findByRole('heading', { name: /статистика/i })).toBeInTheDocument()

  await userEvent.setup().click(screen.getByRole('button', { name: /выйти/i }))
  expect(await screen.findByRole('button', { name: /войти/i })).toBeInTheDocument()
})
