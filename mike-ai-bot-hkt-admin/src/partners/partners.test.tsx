import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { authApi } from '../auth/authApi'
import { failLogoLink, failLogoStorage, restoreLogoLink } from '../test/mockBackend'

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

const PNG_BYTES = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 0])

function pngFile(name = 'logo.png'): File {
  return new File([PNG_BYTES], name, { type: 'image/png' })
}

async function openPartnerEdit(user: ReturnType<typeof userEvent.setup>, name: string) {
  const row = (await screen.findByText(name)).closest('tr')!
  await user.click(within(row).getByRole('button', { name: /действия/i }))
  await user.click(screen.getByRole('menuitem', { name: /изменить/i }))
  return row
}

async function fillNewPartner(user: ReturnType<typeof userEvent.setup>, dialog: HTMLElement) {
  await user.type(within(dialog).getByLabelText(/^имя$/i), 'Test Dive')
  await user.selectOptions(within(dialog).getByLabelText(/^тип$/i), 'excursions')
  await user.type(within(dialog).getByLabelText(/referral/i), 'https://example.com/dive')
}

test('admin creates a partner with a logo picked in the create form', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')
  await user.click(await screen.findByRole('button', { name: /добавить партнёра/i }))
  const dialog = await screen.findByRole('dialog')
  await fillNewPartner(user, dialog)

  await user.upload(within(dialog).getByLabelText(/^логотип$/i), pngFile())

  const preview = await within(dialog).findByRole('img', { name: /предпросмотр логотипа/i })
  expect(preview.getAttribute('src')).toMatch(/^https:\/\/cdn-test\.mikephuketai\.com\/tmp\//)

  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  const row = (await screen.findByText('Test Dive')).closest('tr')!
  const logo = within(row).getByRole('img', { name: /логотип test dive/i })
  expect(logo.getAttribute('src')).toMatch(/^https:\/\/cdn-test\.mikephuketai\.com\/partners\//)
})

async function openCreateWithPartnerFilled() {
  const user = userEvent.setup({ applyAccept: false })
  await renderAuthed('/partners')
  await user.click(await screen.findByRole('button', { name: /добавить партнёра/i }))
  const dialog = await screen.findByRole('dialog')
  await fillNewPartner(user, dialog)
  return { user, dialog }
}

test('wrong logo format is rejected on pick and blocks saving', async () => {
  const { user, dialog } = await openCreateWithPartnerFilled()

  const webp = new File([new Uint8Array([0x52, 0x49, 0x46, 0x46])], 'logo.webp', { type: 'image/webp' })
  await user.upload(within(dialog).getByLabelText(/^логотип$/i), webp)

  expect(await within(dialog).findByRole('alert')).toHaveTextContent('Только JPEG или PNG')
  expect(within(dialog).queryByRole('img', { name: /предпросмотр/i })).not.toBeInTheDocument()
  expect(within(dialog).getByRole('button', { name: /сохранить/i })).toBeDisabled()
})

test('admin can drop a rejected file and save the partner without a logo', async () => {
  const { user, dialog } = await openCreateWithPartnerFilled()
  const webp = new File([new Uint8Array([0x52, 0x49, 0x46, 0x46])], 'logo.webp', { type: 'image/webp' })
  await user.upload(within(dialog).getByLabelText(/^логотип$/i), webp)

  await user.click(within(dialog).getByRole('button', { name: /убрать файл/i }))
  expect(within(dialog).queryByRole('alert')).not.toBeInTheDocument()
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  const row = (await screen.findByText('Test Dive')).closest('tr')!
  expect(within(row).queryByRole('img')).not.toBeInTheDocument()
})

test('if linking the logo fails, the partner is kept and saving again only retries the logo', async () => {
  failLogoLink()
  const { user, dialog } = await openCreateWithPartnerFilled()
  await user.upload(within(dialog).getByLabelText(/^логотип$/i), pngFile())
  await within(dialog).findByRole('img', { name: /предпросмотр логотипа/i })

  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(await within(dialog).findByRole('alert')).toHaveTextContent(
    'Партнёр создан, но логотип не загрузился: Хранилище недоступно, попробуйте позже',
  )
  expect(await screen.findByText('Test Dive')).toBeInTheDocument()

  restoreLogoLink()
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(await screen.findAllByText('Test Dive')).toHaveLength(1)
  const row = screen.getByText('Test Dive').closest('tr')!
  expect(within(row).getByRole('img', { name: /логотип test dive/i })).toBeInTheDocument()
})

test('edit dialog shows the current logo and can remove it', async () => {
  const { user, dialog } = await openCreateWithPartnerFilled()
  await user.upload(within(dialog).getByLabelText(/^логотип$/i), pngFile())
  await within(dialog).findByRole('img', { name: /предпросмотр логотипа/i })
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))
  const row = (await screen.findByText('Test Dive')).closest('tr')!
  const listed = within(row).getByRole('img', { name: /логотип test dive/i }).getAttribute('src')

  await openPartnerEdit(user, 'Test Dive')
  const editDialog = await screen.findByRole('dialog')
  const current = await within(editDialog).findByRole('img', { name: /предпросмотр логотипа/i })
  expect(current.getAttribute('src')).toBe(listed)

  await user.click(within(editDialog).getByRole('button', { name: /удалить логотип/i }))

  expect(within(editDialog).queryByRole('img', { name: /предпросмотр/i })).not.toBeInTheDocument()
  await user.click(within(editDialog).getByRole('button', { name: /отмена/i }))
  const refreshed = (await screen.findByText('Test Dive')).closest('tr')!
  expect(within(refreshed).queryByRole('img')).not.toBeInTheDocument()
})

test('logo over 5 MB is rejected on pick', async () => {
  const { user, dialog } = await openCreateWithPartnerFilled()

  const big = new File([PNG_BYTES, new Uint8Array(5 * 1024 * 1024)], 'big.png', { type: 'image/png' })
  await user.upload(within(dialog).getByLabelText(/^логотип$/i), big)

  expect(await within(dialog).findByRole('alert')).toHaveTextContent('Файл больше 5 МБ')
  expect(within(dialog).getByRole('button', { name: /сохранить/i })).toBeDisabled()
})

test('unreachable storage is reported on pick', async () => {
  failLogoStorage()
  const { user, dialog } = await openCreateWithPartnerFilled()

  await user.upload(within(dialog).getByLabelText(/^логотип$/i), pngFile())

  expect(await within(dialog).findByRole('alert')).toHaveTextContent(
    'Хранилище недоступно, попробуйте позже',
  )
  expect(within(dialog).getByRole('button', { name: /сохранить/i })).toBeDisabled()
})

test('admin can edit a partner in a modal and see updates on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')

  await openPartnerEdit(user, 'Money Shop')

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

  await openPartnerEdit(user, 'Money Shop')

  const dialog = await screen.findByRole('dialog')
  await user.click(within(dialog).getByLabelText(/^активен$/i))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByText('Money Shop')).toBeInTheDocument()
  expect(screen.getByText('Money Shop').closest('tr')).toHaveTextContent('Нет')
})

test('partner list pages eight rows at a time', async () => {
  const user = userEvent.setup()
  await renderAuthed('/partners')

  expect(await screen.findByText('5 партнёров')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /предыдущая страница/i })).toBeDisabled()
  expect(screen.getByRole('button', { name: /следующая страница/i })).toBeDisabled()

  for (let index = 1; index <= 4; index += 1) {
    await user.click(screen.getByRole('button', { name: /добавить партнёра/i }))
    const dialog = await screen.findByRole('dialog')
    await user.type(within(dialog).getByLabelText(/^имя$/i), `Pager ${index}`)
    await user.selectOptions(within(dialog).getByLabelText(/^тип$/i), 'excursions')
    await user.type(within(dialog).getByLabelText(/referral/i), `https://example.com/p${index}`)
    await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))
    expect(await screen.findByText(`Pager ${index}`)).toBeInTheDocument()
  }

  expect(screen.getByText('9 партнёров')).toBeInTheDocument()
  expect(screen.getByText('Pager 4')).toBeInTheDocument()
  expect(screen.queryByText('Money Shop')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: /следующая страница/i })).toBeDisabled()

  await user.click(screen.getByRole('button', { name: /предыдущая страница/i }))

  expect(await screen.findByText('Money Shop')).toBeInTheDocument()
  expect(screen.queryByText('Pager 4')).not.toBeInTheDocument()
})
