import { render, screen, within } from '@testing-library/react'
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

test('authenticated admin sees seeded partners with human type labels', async () => {
  await renderAuthed('/partners')

  expect(screen.getByRole('heading', { name: /партнёры/i })).toBeInTheDocument()
  expect(await screen.findByText('Money Shop')).toBeInTheDocument()
  expect(screen.getByText('Money Shop').closest('tr')).toHaveTextContent('💰 Обмен')
  expect(screen.getByText('Остров Сокровищ').closest('tr')).toHaveTextContent('🇹🇭 Экскурсии')
  expect(screen.getByText('Boomerang').closest('tr')).toHaveTextContent('🛵 Аренда транспорта')
  expect(screen.getByText('Mike eSIM').closest('tr')).toHaveTextContent('📱 eSIM')
  expect(screen.queryByText('money_exchange')).not.toBeInTheDocument()
})

test('admin creates a partner in a modal', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')

  await user.click(await screen.findByRole('button', { name: /добавить партнёра/i }))

  const dialog = await screen.findByRole('dialog')
  expect(within(dialog).queryByLabelText(/logo|лого/i)).not.toBeInTheDocument()

  await user.type(within(dialog).getByLabelText(/^имя$/i), 'Test Dive')
  await user.selectOptions(within(dialog).getByLabelText(/^тип$/i), 'excursions')
  await user.type(within(dialog).getByLabelText(/referral/i), 'https://example.com/dive')
  await user.type(within(dialog).getByLabelText(/описание/i), 'Дайвинг-партнёр')
  await user.clear(within(dialog).getByLabelText(/порядок/i))
  await user.type(within(dialog).getByLabelText(/порядок/i), '5')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(await screen.findByText('Test Dive')).toBeInTheDocument()
})

test('admin can edit a partner in a modal and see updates on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')

  const row = (await screen.findByText('Money Shop')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: /изменить/i }))

  const dialog = await screen.findByRole('dialog')
  const name = within(dialog).getByLabelText(/^имя$/i)
  await user.clear(name)
  await user.type(name, 'Money Shop Updated')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(await screen.findByText('Money Shop Updated')).toBeInTheDocument()
})

test('admin can deactivate a partner via modal', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')

  const row = (await screen.findByText('Money Shop')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: /изменить/i }))

  const dialog = await screen.findByRole('dialog')
  await user.click(within(dialog).getByLabelText(/^активен$/i))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByText('Money Shop')).toBeInTheDocument()
  expect(screen.getByText('Money Shop').closest('tr')).toHaveTextContent('нет')
})
