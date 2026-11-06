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

async function typeItem(topic: string) {
  const panel = await screen.findByRole('complementary', { name: /типы партнёров/i })
  const item = within(panel).getByText(topic).closest('li')
  if (!item) throw new Error(`no type row for ${topic}`)
  return item
}

async function openType(user: ReturnType<typeof userEvent.setup>, topic: string) {
  const item = await typeItem(topic)
  await user.click(within(item).getByRole('button', { name: /действия/i }))
  await user.click(screen.getByRole('menuitem', { name: /изменить/i }))
}

test('old partner types url opens the partners page with the types column', async () => {
  await renderAuthed('/partner-types')

  expect(await screen.findByRole('heading', { name: /^партнёры$/i })).toBeInTheDocument()
  const panel = await screen.findByRole('complementary', { name: /типы партнёров/i })
  expect(within(panel).getByRole('heading', { name: /типы партнёров/i })).toBeInTheDocument()
  expect(within(panel).getByText('💰 Обмен')).toBeInTheDocument()
  expect(within(panel).getByText('🛵 Аренда транспорта')).toBeInTheDocument()
  expect(within(panel).getByText('🇹🇭 Экскурсии')).toBeInTheDocument()
  expect(within(panel).getByText('📱 eSIM')).toBeInTheDocument()
})

test('shows HTTP status when partner types fail to load', async () => {
  failPartnerTypesList(500, 'column "follow_up_text" does not exist')
  await renderAuthed('/partners')

  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Не удалось загрузить типы партнёров (500: column "follow_up_text" does not exist)',
  )
})

test('invalid token while loading partner types sends the admin back to login', async () => {
  failPartnerTypesList(401, 'Invalid token')
  await renderAuthed('/partners')

  expect(await screen.findByRole('button', { name: /войти/i })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: /типы партнёров/i })).not.toBeInTheDocument()
})

test('admin can create a partner type in a modal and see it on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')

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
  const panel = await screen.findByRole('complementary', { name: /типы партнёров/i })
  expect(await within(panel).findByText('🤿 Дайвинг')).toBeInTheDocument()
})

test('admin can set the phrase that finishes “users who chose”', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')

  await openType(user, '💰 Обмен')

  const dialog = await screen.findByRole('dialog')
  const phrase = within(dialog).getByLabelText(/фраза «выбравших»/i)
  expect(phrase).toHaveValue('обмен рублей')
  await user.clear(phrase)
  await user.type(phrase, 'обмен валюты')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  await openType(user, '💰 Обмен')
  expect(within(await screen.findByRole('dialog')).getByLabelText(/фраза «выбравших»/i)).toHaveValue(
    'обмен валюты',
  )
})

test('admin can edit partner type copy in a modal and see updates on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')

  await openType(user, '💰 Обмен')

  const dialog = await screen.findByRole('dialog')
  const topic = within(dialog).getByLabelText(/тема в статистике/i)
  await user.clear(topic)
  await user.type(topic, '💰 Обмен NEW')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  const panel = await screen.findByRole('complementary', { name: /типы партнёров/i })
  expect(await within(panel).findByText('💰 Обмен NEW')).toBeInTheDocument()
})

test('admin can rename partner type slug from the types column', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')

  await openType(user, '💰 Обмен')

  const dialog = await screen.findByRole('dialog')
  const slug = within(dialog).getByLabelText(/^slug$/i)
  await user.clear(slug)
  await user.type(slug, 'fx_exchange')
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  await openType(user, '💰 Обмен')
  expect(within(await screen.findByRole('dialog')).getByLabelText(/^slug$/i)).toHaveValue('fx_exchange')
})

test('admin can toggle is_menu_visible for a partner type in a modal', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')

  await openType(user, '🛵 Аренда транспорта')

  const dialog = await screen.findByRole('dialog')
  expect(within(dialog).getByLabelText(/видно в меню/i)).toBeChecked()
  await user.click(within(dialog).getByLabelText(/видно в меню/i))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  const item = await typeItem('🛵 Аренда транспорта')
  expect(item).toHaveTextContent('Скрыт')
  expect(item).not.toHaveTextContent('В меню')
})
