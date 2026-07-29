import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { authApi } from '../auth/authApi'

async function renderAuthed(path: string) {
  await authApi.login({ email: 'admin@example.com', password: 'admin123' })
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

test('authenticated admin sees KPI totals on stats page', async () => {
  await renderAuthed('/stats')

  expect(screen.getByRole('heading', { name: /статистика/i })).toBeInTheDocument()
  expect(await screen.findByText(/всего пользователей/i)).toBeInTheDocument()
  expect(screen.getByText('128')).toBeInTheDocument()
  expect(screen.getByText(/активны сегодня/i)).toBeInTheDocument()
  expect(screen.getByText(/лиды \(всего\)/i)).toBeInTheDocument()
})

test('authenticated admin sees topic breakdown all-time and 7d', async () => {
  await renderAuthed('/stats')

  expect(await screen.findByRole('heading', { name: /темы \(всё время\)/i })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /темы \(7 дней\)/i })).toBeInTheDocument()
  expect(screen.getAllByText('beaches').length).toBeGreaterThanOrEqual(1)
  expect(screen.getAllByText('ask_mike').length).toBeGreaterThanOrEqual(1)
})

test('authenticated admin sees users by first_source', async () => {
  await renderAuthed('/stats')

  expect(await screen.findByRole('heading', { name: /источники пользователей/i })).toBeInTheDocument()
  expect(screen.getByText('instagram')).toBeInTheDocument()
  expect(screen.getByText('25')).toBeInTheDocument()
  expect(screen.getByText('unknown')).toBeInTheDocument()
})
