import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { authApi } from '../auth/authApi'
import { failPartnerTypesList } from '../test/mockBackend'

async function renderAuthed(path: string) {
  await authApi.login({ email: 'admin@example.com', password: 'admin123' })
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

test('authenticated admin sees seeded partner types on the list', async () => {
  await renderAuthed('/partner-types')

  expect(screen.getByRole('heading', { name: /типы партнёров/i })).toBeInTheDocument()
  expect(await screen.findByText('money_exchange')).toBeInTheDocument()
  expect(screen.getByText('vehicle_rental')).toBeInTheDocument()
  expect(screen.getByText('excursions')).toBeInTheDocument()
  expect(screen.getByText('esim')).toBeInTheDocument()
})

test('shows HTTP status when partner types fail to load', async () => {
  failPartnerTypesList(500, 'column "follow_up_text" does not exist')
  await renderAuthed('/partner-types')

  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Не удалось загрузить типы партнёров (500: column "follow_up_text" does not exist)',
  )
})

test('invalid token while loading partner types sends the admin back to login', async () => {
  failPartnerTypesList(401, 'Invalid token')
  await renderAuthed('/partner-types')

  expect(await screen.findByRole('button', { name: /войти/i })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: /типы партнёров/i })).not.toBeInTheDocument()
})

test('admin can create a partner type in a modal and see it on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-types')

  await user.click(await screen.findByRole('button', { name: /добавить тип/i }))

  const dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/^slug$/i), 'diving')
  await user.clear(within(dialog).getByLabelText(/порядок/i))
  await user.type(within(dialog).getByLabelText(/порядок/i), '40')
  await user.type(within(dialog).getByLabelText(/кнопка меню/i), '🤿 Дайвинг')
  await user.type(within(dialog).getByLabelText(/тема в статистике/i), '🤿 Дайвинг')
  await user.type(within(dialog).getByLabelText(/^intro$/i), 'Партнёры по дайвингу:')
  await user.type(within(dialog).getByLabelText(/^fallback$/i), 'Пока нет партнёров.')
  await user.type(within(dialog).getByLabelText(/emoji подписи/i), '🤿')
  await user.type(within(dialog).getByLabelText(/cta подписи/i), '⬇️ Записаться ⬇️')
  await user.type(within(dialog).getByLabelText(/шаблон кнопки/i), 'Записаться у {name}')
  await user.type(within(dialog).getByLabelText(/фраза «выбравших»/i), 'дайвинг')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(await screen.findByText('diving')).toBeInTheDocument()
})

test('admin can set the phrase that finishes “users who chose”', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-types')

  const row = (await screen.findByText('money_exchange')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: /изменить/i }))

  const dialog = await screen.findByRole('dialog')
  const phrase = within(dialog).getByLabelText(/фраза «выбравших»/i)
  expect(phrase).toHaveValue('обмен рублей')
  await user.clear(phrase)
  await user.type(phrase, 'обмен валюты')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  await user.click(within(row).getByRole('button', { name: /изменить/i }))
  expect(within(await screen.findByRole('dialog')).getByLabelText(/фраза «выбравших»/i)).toHaveValue(
    'обмен валюты',
  )
})

test('admin can edit partner type copy in a modal and see updates on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-types')

  const row = (await screen.findByText('money_exchange')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: /изменить/i }))

  const dialog = await screen.findByRole('dialog')
  const topic = within(dialog).getByLabelText(/тема в статистике/i)
  await user.clear(topic)
  await user.type(topic, '💰 Обмен NEW')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(await screen.findByText('💰 Обмен NEW')).toBeInTheDocument()
})

test('admin can rename partner type slug in a modal and see the new slug on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-types')

  const row = (await screen.findByText('money_exchange')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: /изменить/i }))

  const dialog = await screen.findByRole('dialog')
  const slug = within(dialog).getByLabelText(/^slug$/i)
  await user.clear(slug)
  await user.type(slug, 'fx_exchange')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByText('fx_exchange')).toBeInTheDocument()
  expect(screen.queryByText('money_exchange')).not.toBeInTheDocument()
})

test('admin can toggle is_menu_visible for a partner type in a modal', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-types')

  const row = (await screen.findByText('vehicle_rental')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: /изменить/i }))

  const dialog = await screen.findByRole('dialog')
  expect(within(dialog).getByLabelText(/видно в меню/i)).toBeChecked()
  await user.click(within(dialog).getByLabelText(/видно в меню/i))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByText('vehicle_rental')).toBeInTheDocument()
  expect(screen.getByText('vehicle_rental').closest('tr')).toHaveTextContent('нет')
})
