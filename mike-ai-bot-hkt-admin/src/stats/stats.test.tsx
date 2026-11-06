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
  const users = (await screen.findByText(/всего пользователей/i)).closest('article')!
  expect(within(users).getByText('128')).toBeInTheDocument()
  expect(screen.getByText(/активные сегодня/i)).toBeInTheDocument()
  expect(screen.getByText(/лиды \(всего\)/i)).toBeInTheDocument()
})

test('authenticated admin sees topic and source donut sections without 7-day topics', async () => {
  await renderAuthed('/stats')

  expect(await screen.findByRole('heading', { name: /популярные темы/i })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /источники пользователей/i })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: /темы \(7 дней\)/i })).not.toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: /темы \(всё время\)/i })).not.toBeInTheDocument()
})

test('popular topics legend strips emoji and shows share percents', async () => {
  await renderAuthed('/stats')

  const heading = await screen.findByRole('heading', { name: /популярные темы/i })
  const section = heading.closest('div')!
  expect(within(section).getByText('Пляжи')).toBeInTheDocument()
  expect(within(section).getByText('Спросить Майка')).toBeInTheDocument()
  expect(within(section).getByText('Обмен')).toBeInTheDocument()
  expect(within(section).queryByText(/🏖/)).not.toBeInTheDocument()
  expect(within(section).getByText('38%')).toBeInTheDocument()
  expect(within(section).getByText('35%')).toBeInTheDocument()
  expect(within(section).getByText('27%')).toBeInTheDocument()
})

test('user sources legend uses Russian labels for known sources', async () => {
  await renderAuthed('/stats')

  const heading = await screen.findByRole('heading', { name: /источники пользователей/i })
  const section = heading.closest('div')!
  expect(within(section).getByText('Неизвестно')).toBeInTheDocument()
  expect(within(section).getByText('Instagram')).toBeInTheDocument()
  expect(within(section).getByText('Facebook')).toBeInTheDocument()
  expect(within(section).queryByText('unknown')).not.toBeInTheDocument()
  expect(within(section).queryByText('instagram')).not.toBeInTheDocument()
  expect(within(section).getByText('70%')).toBeInTheDocument()
})

test('stats page shows signed delta pills and the seven activity days', async () => {
  await renderAuthed('/stats')

  const users = (await screen.findByText(/всего пользователей/i)).closest('article')!
  expect(within(users).getByText('+12%')).toBeInTheDocument()

  const leads = screen.getByText(/лиды \(всего\)/i).closest('article')!
  expect(within(leads).getByText('-50%')).toBeInTheDocument()

  const weekLeads = screen.getByText(/лиды \(7 дней\)/i).closest('article')!
  expect(within(weekLeads).getByText('-25%')).toBeInTheDocument()

  const today = screen.getByText(/новые сегодня/i).closest('article')!
  expect(within(today).getByText('0%')).toBeInTheDocument()

  const active = screen.getByText(/активные сегодня/i).closest('article')!
  expect(within(active).getByText('+100%')).toBeInTheDocument()

  const activity = screen.getByRole('region', { name: /динамика активности/i })
  expect(within(activity).getByText('31 окт')).toBeInTheDocument()
  expect(within(activity).getByText('6 ноя')).toBeInTheDocument()
  expect(within(activity).getByText('3')).toBeInTheDocument()
})
