import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { authApi } from '../auth/authApi'

test('stats page shows map opens beside saved tourists', async () => {
  await authApi.login({ email: 'shop@example.com', password: 'shop-secret' })
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  const saved = await screen.findByText('В избранном')
  const opened = screen.getByText('Открыто в Картах')
  const category = screen.getByText('Пользователей, выбравших обмен рублей (всё время)')
  expect(saved.compareDocumentPosition(opened) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  expect(opened.compareDocumentPosition(category) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  expect(screen.getByText('11')).toBeInTheDocument()
})

test('stats page shows tourists who saved the current partner above category users', async () => {
  await authApi.login({ email: 'shop@example.com', password: 'shop-secret' })
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  const saved = await screen.findByText('В избранном')
  const category = screen.getByText('Пользователей, выбравших обмен рублей (всё время)')
  expect(saved.compareDocumentPosition(category) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  expect(screen.getByText('9')).toBeInTheDocument()
})

test('stats page shows users who chose the partner category above views', async () => {
  await authApi.login({ email: 'shop@example.com', password: 'shop-secret' })
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  const allTime = await screen.findByText('Пользователей, выбравших обмен рублей (всё время)')
  const last30 = screen.getByText('Пользователей, выбравших обмен рублей (30 дней)')
  const views = screen.getByText('Показы (всё время)')
  expect(allTime.compareDocumentPosition(views) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  expect(last30.compareDocumentPosition(views) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  expect(screen.getByText('42')).toBeInTheDocument()
  expect(screen.getByText('7')).toBeInTheDocument()
})

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
