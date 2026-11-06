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

test('admin can create a place category and see it on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/place-categories')

  await user.click(await screen.findByRole('button', { name: /добавить категорию/i }))

  const dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/^slug$/i), 'viewpoint')
  await user.type(within(dialog).getByLabelText(/название/i), 'Смотровая')
  await user.clear(within(dialog).getByLabelText(/порядок/i))
  await user.type(within(dialog).getByLabelText(/порядок/i), '60')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(await screen.findByText('viewpoint')).toBeInTheDocument()
  expect(screen.getByText('Смотровая')).toBeInTheDocument()
})

test('admin can rename a place category label and the slug stays', async () => {
  const user = userEvent.setup()
  await renderAuthed('/place-categories')

  const row = (await screen.findByText('beach')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: /изменить/i }))

  const dialog = await screen.findByRole('dialog')
  expect(within(dialog).getByLabelText(/^slug$/i)).toBeDisabled()
  const label = within(dialog).getByLabelText(/название/i)
  await user.clear(label)
  await user.type(label, 'Пляжи')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByText('Пляжи')).toBeInTheDocument()
  expect(screen.getByText('beach')).toBeInTheDocument()
})

test('a category used by a place has no delete control', async () => {
  await renderAuthed('/places?tab=categories')

  const row = (await screen.findByText('shop')).closest('tr')!
  expect(within(row).queryByRole('button', { name: /удалить/i })).not.toBeInTheDocument()
  expect(within(row).getByRole('button', { name: /изменить/i })).toBeInTheDocument()
})

test('admin can delete a place category that no place uses', async () => {
  const user = userEvent.setup()
  await renderAuthed('/place-categories')

  const row = (await screen.findByText('cafe')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: /удалить/i }))

  expect(screen.queryByText('cafe')).not.toBeInTheDocument()
  expect(screen.getByText('beach')).toBeInTheDocument()
})
