import { cleanup, render, screen } from '@testing-library/react'
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

test('authenticated admin sees seeded partners on the list', async () => {
  await renderAuthed('/partners')

  expect(screen.getByRole('heading', { name: /партнёры/i })).toBeInTheDocument()
  expect(await screen.findByText('Money Shop')).toBeInTheDocument()
  expect(screen.getByText('Ex24.pro')).toBeInTheDocument()
  expect(screen.getByText('Остров Сокровищ')).toBeInTheDocument()
})

test('admin can create a partner without logo and see it on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners/new')

  expect(screen.queryByLabelText(/logo|лого/i)).not.toBeInTheDocument()

  await user.type(await screen.findByLabelText(/^имя$/i), 'Test Dive')
  await user.selectOptions(await screen.findByLabelText(/^тип$/i), 'excursions')
  await user.type(await screen.findByLabelText(/referral/i), 'https://example.com/dive')
  await user.type(await screen.findByLabelText(/описание/i), 'Дайвинг-партнёр')
  await user.clear(await screen.findByLabelText(/порядок/i))
  await user.type(await screen.findByLabelText(/порядок/i), '5')
  await user.click(screen.getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByRole('heading', { name: /партнёры/i })).toBeInTheDocument()
  expect(screen.getByText('Test Dive')).toBeInTheDocument()
})

test('admin can edit a partner and see updates on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners/00000000-0000-4000-8000-000000000001/edit')

  const name = await screen.findByLabelText(/^имя$/i)
  await user.clear(name)
  await user.type(name, 'Money Shop Updated')
  await user.click(screen.getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByRole('heading', { name: /партнёры/i })).toBeInTheDocument()
  expect(screen.getByText('Money Shop Updated')).toBeInTheDocument()
})

test('admin can deactivate a partner', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners/00000000-0000-4000-8000-000000000001/edit')

  await user.click(await screen.findByLabelText(/^активен$/i))
  await user.click(screen.getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByRole('heading', { name: /партнёры/i })).toBeInTheDocument()
  const row = screen.getByText('Money Shop').closest('tr')
  expect(row).toHaveTextContent('нет')
})

test('renaming a partner type slug cascades to partners of that type', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-types/money_exchange/edit')

  const slug = await screen.findByLabelText(/^slug$/i)
  await user.clear(slug)
  await user.type(slug, 'fx_exchange')
  await user.click(screen.getByRole('button', { name: /сохранить/i }))
  expect(await screen.findByRole('heading', { name: /типы партнёров/i })).toBeInTheDocument()

  cleanup()
  await renderAuthed('/partners')

  expect(await screen.findByText('Money Shop')).toBeInTheDocument()
  expect(screen.getByText('Money Shop').closest('tr')).toHaveTextContent('fx_exchange')
  expect(screen.getByText('Ex24.pro').closest('tr')).toHaveTextContent('fx_exchange')
  expect(screen.getByText('Остров Сокровищ').closest('tr')).toHaveTextContent('excursions')
})
