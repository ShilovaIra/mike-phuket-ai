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

test('knowledge base shows a listed partner with its referral link and that Mike uses it', async () => {
  await renderAuthed('/knowledge-base')

  expect(screen.getByRole('heading', { name: /база знаний/i })).toBeInTheDocument()
  const row = (await screen.findByText('Money Shop')).closest('tr')!
  expect(row).toHaveTextContent('💰 Обмен')
  expect(row).toHaveTextContent('https://moneyshopphuket.online/links/pp413')
  expect(row).toHaveTextContent('В чате: да')
})

test('an unlisted partner stays on the knowledge base but is not in chat', async () => {
  await renderAuthed('/knowledge-base')

  const row = (await screen.findByText('Ex24.pro')).closest('tr')!
  expect(row).toHaveTextContent('https://ex24qr.com/epihelgnld')
  expect(row).toHaveTextContent('В чате: нет')
})

test('a place row shows its map link and the listed partner referral', async () => {
  await renderAuthed('/knowledge-base')

  const row = (await screen.findByText('Reef Divers Pier')).closest('tr')!
  expect(row).toHaveTextContent('https://maps.example/reef')
  expect(row).toHaveTextContent('https://example.com/reef')
  expect(row).toHaveTextContent('В чате: да')
})

test('operator adds a partner from the mixed list and it is no longer offered', async () => {
  const user = userEvent.setup()
  await renderAuthed('/knowledge-base')

  await user.click(await screen.findByRole('button', { name: /добавить/i }))
  const dialog = await screen.findByRole('dialog')
  const select = within(dialog).getByRole('combobox')
  await user.selectOptions(select, within(select).getByRole('option', { name: /boomerang/i }))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  const row = (await screen.findByText('Boomerang')).closest('tr')!
  expect(row).toHaveTextContent('https://boomerang.rent/catalog/?utm_source=MikePhuketAIBot')
  expect(row).toHaveTextContent('В чате: да')

  await user.click(screen.getByRole('button', { name: /добавить/i }))
  const again = await screen.findByRole('dialog')
  expect(within(again).queryByRole('option', { name: /boomerang/i })).not.toBeInTheDocument()
})

test('picker hides a partner when its place is already in the knowledge base', async () => {
  const user = userEvent.setup()
  await renderAuthed('/knowledge-base')

  await user.click(await screen.findByRole('button', { name: /добавить/i }))
  const dialog = await screen.findByRole('dialog')
  expect(within(dialog).queryByRole('option', { name: /остров сокровищ/i })).not.toBeInTheDocument()
})

test('removing a row lets the operator add that business again', async () => {
  const user = userEvent.setup()
  await renderAuthed('/knowledge-base')

  const row = (await screen.findByText('Money Shop')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: /удалить/i }))

  expect(screen.queryByText('Money Shop')).not.toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: /добавить/i }))
  const dialog = await screen.findByRole('dialog')
  expect(within(dialog).getByRole('option', { name: /money shop/i })).toBeInTheDocument()
})
