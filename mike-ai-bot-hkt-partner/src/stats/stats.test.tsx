import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { authApi } from '../auth/authApi'

test('stats page shows all-time and last 30 days totals', async () => {
  await authApi.login({ email: 'shop@example.com', password: 'shop-secret' })
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  expect(await screen.findByText('Показы (всё время)')).toBeInTheDocument()
  expect(screen.getByText('Переходы (всё время)')).toBeInTheDocument()
  expect(screen.getByText('Показы (30 дней)')).toBeInTheDocument()
  expect(screen.getByText('10')).toBeInTheDocument()
  expect(screen.getByText('5')).toBeInTheDocument()
})

test('stats donut names views with and without a referral click', async () => {
  await authApi.login({ email: 'shop@example.com', password: 'shop-secret' })
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  expect(await screen.findByText('Показы с переходом')).toBeInTheDocument()
  expect(screen.getByText('Показы без перехода')).toBeInTheDocument()
})

test('stats cards show views and referral clicks only', async () => {
  await authApi.login({ email: 'shop@example.com', password: 'shop-secret' })
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  expect(await screen.findByText('Показы (всё время)')).toBeInTheDocument()
  expect(screen.getByText('Переходы (всё время)')).toBeInTheDocument()
  expect(screen.queryAllByText(/открытые показы/i)).toHaveLength(0)
})

test('stats donut is a named region without a heading', async () => {
  await authApi.login({ email: 'shop@example.com', password: 'shop-secret' })
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  expect(
    await screen.findByRole('region', { name: /показы с переходом и без/i }),
  ).toBeInTheDocument()
  expect(
    screen.queryByRole('heading', { name: /показы: переход или нет/i }),
  ).not.toBeInTheDocument()
})
