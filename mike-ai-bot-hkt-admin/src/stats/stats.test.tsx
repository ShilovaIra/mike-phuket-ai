import { render, screen, within } from '@testing-library/react'
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

test('authenticated admin sees labeled topics and readable column headers', async () => {
  await renderAuthed('/stats')

  const allTime = await screen.findByRole('heading', { name: /темы \(всё время\)/i })
  const allTimeSection = allTime.closest('div')!
  expect(within(allTimeSection).getByRole('columnheader', { name: 'Пользователи' })).toBeInTheDocument()
  expect(within(allTimeSection).getByRole('columnheader', { name: 'Нажатия' })).toBeInTheDocument()
  expect(within(allTimeSection).getByText('🏖 Пляжи')).toBeInTheDocument()
  expect(within(allTimeSection).getByText('💬 Спросить Майка')).toBeInTheDocument()
  expect(within(allTimeSection).getByText('💰 Обмен')).toBeInTheDocument()
  expect(within(allTimeSection).queryByText('beaches')).not.toBeInTheDocument()
  expect(within(allTimeSection).queryByText('ask_mike')).not.toBeInTheDocument()

  expect(screen.getByRole('heading', { name: /темы \(7 дней\)/i })).toBeInTheDocument()
})

test('authenticated admin sees users by first_source with Russian column header', async () => {
  await renderAuthed('/stats')

  const heading = await screen.findByRole('heading', { name: /источники пользователей/i })
  const section = heading.closest('section')!
  expect(within(section).getByRole('columnheader', { name: 'Источник' })).toBeInTheDocument()
  expect(within(section).queryByText('first_source')).not.toBeInTheDocument()
  expect(within(section).getByText('instagram')).toBeInTheDocument()
  expect(within(section).getByText('25')).toBeInTheDocument()
  expect(within(section).getByText('unknown')).toBeInTheDocument()
})
