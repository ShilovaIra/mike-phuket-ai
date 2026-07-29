import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

test('authenticated admin sees seeded partner types on the list', async () => {
  await renderAuthed('/partner-types')

  expect(screen.getByRole('heading', { name: /типы партнёров/i })).toBeInTheDocument()
  expect(await screen.findByText('money_exchange')).toBeInTheDocument()
  expect(screen.getByText('vehicle_rental')).toBeInTheDocument()
  expect(screen.getByText('excursions')).toBeInTheDocument()
})

test('admin can create a partner type and see it on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-types/new')

  await user.type(await screen.findByLabelText(/^slug$/i), 'diving')
  await user.clear(await screen.findByLabelText(/порядок/i))
  await user.type(await screen.findByLabelText(/порядок/i), '40')
  await user.type(await screen.findByLabelText(/кнопка меню/i), '🤿 Дайвинг')
  await user.type(await screen.findByLabelText(/тема в статистике/i), '🤿 Дайвинг')
  await user.type(await screen.findByLabelText(/^intro$/i), 'Партнёры по дайвингу:')
  await user.type(await screen.findByLabelText(/^fallback$/i), 'Пока нет партнёров.')
  await user.type(await screen.findByLabelText(/emoji подписи/i), '🤿')
  await user.type(await screen.findByLabelText(/cta подписи/i), '⬇️ Записаться ⬇️')
  await user.type(await screen.findByLabelText(/шаблон кнопки/i), 'Записаться у {name}')
  await user.click(screen.getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByRole('heading', { name: /типы партнёров/i })).toBeInTheDocument()
  expect(screen.getByText('diving')).toBeInTheDocument()
})

test('admin can edit partner type copy and see updates on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-types/money_exchange/edit')

  const topic = await screen.findByLabelText(/тема в статистике/i)
  await user.clear(topic)
  await user.type(topic, '💰 Обмен NEW')
  await user.click(screen.getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByRole('heading', { name: /типы партнёров/i })).toBeInTheDocument()
  expect(screen.getByText('💰 Обмен NEW')).toBeInTheDocument()
})

test('admin can rename partner type slug and see the new slug on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-types/money_exchange/edit')

  const slug = await screen.findByLabelText(/^slug$/i)
  await user.clear(slug)
  await user.type(slug, 'fx_exchange')
  await user.click(screen.getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByRole('heading', { name: /типы партнёров/i })).toBeInTheDocument()
  expect(screen.getByText('fx_exchange')).toBeInTheDocument()
  expect(screen.queryByText('money_exchange')).not.toBeInTheDocument()
})

test('admin can toggle is_menu_visible for a partner type', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-types/vehicle_rental/edit')

  expect(await screen.findByLabelText(/видно в меню/i)).not.toBeChecked()
  await user.click(await screen.findByLabelText(/видно в меню/i))
  await user.click(screen.getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByRole('heading', { name: /типы партнёров/i })).toBeInTheDocument()
  const row = screen.getByText('vehicle_rental').closest('tr')
  expect(row).toHaveTextContent('да')
})
