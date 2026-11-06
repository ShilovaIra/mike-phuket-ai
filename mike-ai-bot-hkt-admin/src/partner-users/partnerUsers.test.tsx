import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { authApi } from '../auth/authApi'
import { formatBangkok } from '../broadcasts/formatBangkok'
import { MOCK_PARTNER_USER_CREATED_AT, setPartnerLogoUrl } from '../test/mockBackend'

const MONEY_SHOP = '00000000-0000-4000-8000-000000000001'

async function renderAuthed(path: string) {
  await authApi.login({ email: 'admin@example.com', password: 'admin123' })
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

test('admin creates a partner user with access to a partner', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-users')

  expect(screen.getByRole('heading', { name: /пользователи партнёров/i })).toBeInTheDocument()
  await user.click(await screen.findByRole('button', { name: /добавить пользователя/i }))

  const dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/^email$/i), 'shop@example.com')
  await user.type(within(dialog).getByLabelText(/^пароль$/i), 'shop-secret')
  await user.click(within(dialog).getByLabelText(/money shop/i))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  const row = (await screen.findByText('shop@example.com')).closest('tr')!
  expect(row).toHaveTextContent('Money Shop')
  expect(row).toHaveTextContent(formatBangkok(MOCK_PARTNER_USER_CREATED_AT))
  expect(within(row).queryByRole('img')).not.toBeInTheDocument()
  expect(within(row).getByText('S')).toBeInTheDocument()
})

test('create partner user requires at least one partner', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-users')
  await user.click(await screen.findByRole('button', { name: /добавить пользователя/i }))

  const dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/^email$/i), 'shop@example.com')
  await user.type(within(dialog).getByLabelText(/^пароль$/i), 'shop-secret')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(within(dialog).getByRole('alert')).toHaveTextContent(
    'Выберите хотя бы одного партнёра',
  )
  expect(screen.getByRole('dialog')).toBeInTheDocument()
})

test('a single linked partner shows its logo, several partners show names and an initial', async () => {
  setPartnerLogoUrl(MONEY_SHOP, 'https://cdn-test.mikephuketai.com/money.png')
  const user = userEvent.setup()
  await renderAuthed('/partner-users')
  await user.click(await screen.findByRole('button', { name: /добавить пользователя/i }))

  let dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/^email$/i), 'one@example.com')
  await user.type(within(dialog).getByLabelText(/^пароль$/i), 'shop-secret')
  await user.click(within(dialog).getByLabelText(/^money shop$/i))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  const single = (await screen.findByText('one@example.com')).closest('tr')!
  expect(within(single).getByRole('img', { name: /логотип money shop/i })).toHaveAttribute(
    'src',
    'https://cdn-test.mikephuketai.com/money.png',
  )

  await user.click(screen.getByRole('button', { name: /добавить пользователя/i }))
  dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/^email$/i), 'many@example.com')
  await user.type(within(dialog).getByLabelText(/^пароль$/i), 'shop-secret')
  await user.click(within(dialog).getByLabelText(/^money shop$/i))
  await user.click(within(dialog).getByLabelText(/ex24\.pro/i))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  const many = (await screen.findByText('many@example.com')).closest('tr')!
  expect(many).toHaveTextContent('Money Shop, Ex24.pro')
  expect(within(many).queryByRole('img')).not.toBeInTheDocument()
  expect(within(many).getByText('M')).toBeInTheDocument()
})

test('search and partner filter narrow the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-users')
  await user.click(await screen.findByRole('button', { name: /добавить пользователя/i }))
  const dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/^email$/i), 'shop@example.com')
  await user.type(within(dialog).getByLabelText(/^пароль$/i), 'shop-secret')
  await user.click(within(dialog).getByLabelText(/^money shop$/i))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))
  await screen.findByText('shop@example.com')

  await user.type(screen.getByRole('searchbox', { name: /поиск по email или партнёру/i }), 'ex24')
  expect(screen.queryByText('shop@example.com')).not.toBeInTheDocument()
  expect(screen.getByText(/никого не найдено/i)).toBeInTheDocument()
  await user.clear(screen.getByRole('searchbox', { name: /поиск по email или партнёру/i }))
  expect(await screen.findByText('shop@example.com')).toBeInTheDocument()

  const filter = screen.getByRole('combobox', { name: 'Партнёр' })
  await user.selectOptions(filter, within(filter).getByRole('option', { name: 'Ex24.pro' }))
  expect(screen.queryByText('shop@example.com')).not.toBeInTheDocument()
  await user.selectOptions(filter, within(filter).getByRole('option', { name: 'Все партнёры' }))
  expect(await screen.findByText('shop@example.com')).toBeInTheDocument()
})

test('pencil edits partner access and leaves a blank password unchanged', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partner-users')
  await user.click(await screen.findByRole('button', { name: /добавить пользователя/i }))
  let dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/^email$/i), 'shop@example.com')
  await user.type(within(dialog).getByLabelText(/^пароль$/i), 'shop-secret')
  await user.click(within(dialog).getByLabelText(/^money shop$/i))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  await user.click(await screen.findByRole('button', { name: /изменить: shop@example.com/i }))
  dialog = await screen.findByRole('dialog')
  expect(within(dialog).getByText('shop@example.com')).toBeInTheDocument()
  expect(within(dialog).queryByLabelText(/^email$/i)).not.toBeInTheDocument()
  await user.click(within(dialog).getByLabelText(/^money shop$/i))
  await user.click(within(dialog).getByLabelText(/ex24\.pro/i))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  const row = (await screen.findByText('shop@example.com')).closest('tr')!
  expect(row).toHaveTextContent('Ex24.pro')
  expect(row).not.toHaveTextContent('Money Shop')
})
