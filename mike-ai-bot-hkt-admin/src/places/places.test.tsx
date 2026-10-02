import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import placeholder from '../assets/placeholders/empty_picture_placeholder.jpg'
import { authApi } from '../auth/authApi'
import { failPlacePhotoSave, restorePlacePhotoSave } from '../test/mockBackend'

async function renderAuthed(path: string) {
  await authApi.login({ email: 'admin@example.com', password: 'admin123' })
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

test('admin can create a place and see it on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/places')

  await user.click(await screen.findByRole('button', { name: /добавить место/i }))

  const dialog = await screen.findByRole('dialog')
  await user.type(await within(dialog).findByLabelText(/название/i), 'Мыс Промтеп')
  await user.selectOptions(within(dialog).getByLabelText(/категория/i), 'beach')
  await user.type(within(dialog).getByLabelText(/описание/i), 'Закат')
  await user.type(
    within(dialog).getByLabelText(/ссылка/i),
    'https://www.google.com/maps/place/Promthep/@7.76,98.30,17z',
  )
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(await screen.findByText('Мыс Промтеп')).toBeInTheDocument()
  expect(screen.getByText('Закат')).toBeInTheDocument()
  expect(screen.getByText('Пляж')).toBeInTheDocument()
})

const JPEG_BYTES = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 0, 0, 0, 0])
const PNG_BYTES = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 0])

function jpegFile(name = 'front.jpg'): File {
  return new File([JPEG_BYTES], name, { type: 'image/jpeg' })
}

function pngFile(name = 'front.png'): File {
  return new File([PNG_BYTES], name, { type: 'image/png' })
}

async function createPlaceWithPhoto(user: ReturnType<typeof userEvent.setup>, name: string) {
  await user.click(await screen.findByRole('button', { name: /добавить место/i }))
  const dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/название/i), name)
  await user.selectOptions(within(dialog).getByLabelText(/категория/i), 'beach')
  await user.type(
    within(dialog).getByLabelText(/ссылка/i),
    'https://www.google.com/maps/place/Promthep/@7.76,98.30,17z',
  )
  await user.upload(within(dialog).getByLabelText(/^фото$/i), jpegFile())
  await within(dialog).findByRole('img', { name: /предпросмотр фото/i })
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
}

test('admin creates a place with a photo and sees it on the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/places')

  await user.click(await screen.findByRole('button', { name: /добавить место/i }))
  const dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/название/i), 'Мыс Промтеп')
  await user.selectOptions(within(dialog).getByLabelText(/категория/i), 'beach')
  await user.type(
    within(dialog).getByLabelText(/ссылка/i),
    'https://www.google.com/maps/place/Promthep/@7.76,98.30,17z',
  )
  await user.upload(within(dialog).getByLabelText(/^фото$/i), jpegFile())

  const preview = await within(dialog).findByRole('img', { name: /предпросмотр фото/i })
  expect(preview.getAttribute('src')).toMatch(/^https:\/\/cdn-test\.mikephuketai\.com\/tmp\//)

  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  const row = (await screen.findByText('Мыс Промтеп')).closest('tr')!
  const photo = within(row).getByRole('img', { name: /фото мыс промтеп/i })
  expect(photo.getAttribute('src')).toMatch(/^https:\/\/cdn-test\.mikephuketai\.com\/places\//)
})

test('a place without a photo shows the placeholder', async () => {
  const user = userEvent.setup()
  await renderAuthed('/places')

  await user.click(await screen.findByRole('button', { name: /добавить место/i }))
  const dialog = await screen.findByRole('dialog')
  expect(within(dialog).getByRole('img', { name: /предпросмотр фото/i })).toHaveAttribute(
    'src',
    placeholder,
  )

  await user.type(within(dialog).getByLabelText(/название/i), 'Мыс Промтеп')
  await user.selectOptions(within(dialog).getByLabelText(/категория/i), 'beach')
  await user.type(
    within(dialog).getByLabelText(/ссылка/i),
    'https://www.google.com/maps/place/Promthep/@7.76,98.30,17z',
  )
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  const row = (await screen.findByText('Мыс Промтеп')).closest('tr')!
  expect(within(row).getByRole('img', { name: /фото мыс промтеп/i })).toHaveAttribute(
    'src',
    placeholder,
  )
})

test('replacing a photo updates the list and cancel keeps the current photo', async () => {
  const user = userEvent.setup()
  await renderAuthed('/places')
  await createPlaceWithPhoto(user, 'Мыс Промтеп')

  const row = () => screen.getByText('Мыс Промтеп').closest('tr')!
  const original = within(row()).getByRole('img', { name: /фото мыс промтеп/i }).getAttribute('src')

  await user.click(within(row()).getByRole('button', { name: /изменить/i }))
  let dialog = await screen.findByRole('dialog', { name: /изменить место/i })
  await user.upload(within(dialog).getByLabelText(/^фото$/i), pngFile())
  await user.click(within(dialog).getByRole('button', { name: /отмена/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(within(row()).getByRole('img', { name: /фото мыс промтеп/i })).toHaveAttribute(
    'src',
    original,
  )

  await user.click(within(row()).getByRole('button', { name: /изменить/i }))
  dialog = await screen.findByRole('dialog', { name: /изменить место/i })
  await user.upload(within(dialog).getByLabelText(/^фото$/i), pngFile('new.png'))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  const updated = within(row()).getByRole('img', { name: /фото мыс промтеп/i })
  expect(updated.getAttribute('src')).toMatch(/\.png$/)
  expect(updated.getAttribute('src')).not.toBe(original)
})

test('deleting a photo on save shows the placeholder', async () => {
  const user = userEvent.setup()
  await renderAuthed('/places')
  await createPlaceWithPhoto(user, 'Мыс Промтеп')

  const row = () => screen.getByText('Мыс Промтеп').closest('tr')!
  const original = within(row()).getByRole('img', { name: /фото мыс промтеп/i }).getAttribute('src')

  await user.click(within(row()).getByRole('button', { name: /изменить/i }))
  let dialog = await screen.findByRole('dialog', { name: /изменить место/i })
  await user.click(within(dialog).getByRole('button', { name: /удалить фото/i }))
  expect(within(dialog).getByRole('img', { name: /предпросмотр фото/i })).toHaveAttribute(
    'src',
    placeholder,
  )
  await user.click(within(dialog).getByRole('button', { name: /отмена/i }))

  expect(within(row()).getByRole('img', { name: /фото мыс промтеп/i })).toHaveAttribute(
    'src',
    original,
  )

  await user.click(within(row()).getByRole('button', { name: /изменить/i }))
  dialog = await screen.findByRole('dialog', { name: /изменить место/i })
  await user.click(within(dialog).getByRole('button', { name: /удалить фото/i }))
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(within(row()).getByRole('img', { name: /фото мыс промтеп/i })).toHaveAttribute(
    'src',
    placeholder,
  )
})

test('a failed photo save keeps the place and retries the photo', async () => {
  failPlacePhotoSave()
  const user = userEvent.setup()
  await renderAuthed('/places')

  await user.click(await screen.findByRole('button', { name: /добавить место/i }))
  const dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/название/i), 'Мыс Промтеп')
  await user.selectOptions(within(dialog).getByLabelText(/категория/i), 'beach')
  await user.type(
    within(dialog).getByLabelText(/ссылка/i),
    'https://www.google.com/maps/place/Promthep/@7.76,98.30,17z',
  )
  await user.upload(within(dialog).getByLabelText(/^фото$/i), jpegFile())
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(await within(dialog).findByRole('alert')).toHaveTextContent(
    'Место сохранено, но фото не загрузилось: Хранилище недоступно, попробуйте позже',
  )

  restorePlacePhotoSave()
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(screen.getAllByText('Мыс Промтеп')).toHaveLength(1)
  expect(screen.getByRole('img', { name: /фото мыс промтеп/i }).getAttribute('src')).toMatch(
    /^https:\/\/cdn-test\.mikephuketai\.com\/places\//,
  )
})

test('a failed photo replace keeps the new text and the previous photo', async () => {
  const user = userEvent.setup()
  await renderAuthed('/places')
  await createPlaceWithPhoto(user, 'Мыс Промтеп')

  const row = () => screen.getByText(/промтеп/i).closest('tr')!
  const original = within(row()).getByRole('img', { name: /фото/i }).getAttribute('src')

  await user.click(within(row()).getByRole('button', { name: /изменить/i }))
  const dialog = await screen.findByRole('dialog', { name: /изменить место/i })
  const name = within(dialog).getByLabelText(/название/i)
  await user.clear(name)
  await user.type(name, 'Кап Промтеп')
  await user.upload(within(dialog).getByLabelText(/^фото$/i), pngFile())
  failPlacePhotoSave()
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  expect(await within(dialog).findByRole('alert')).toHaveTextContent(
    'Фото не загрузилось: Хранилище недоступно, попробуйте позже',
  )
  await user.click(within(dialog).getByRole('button', { name: /отмена/i }))

  expect(screen.getByText('Кап Промтеп')).toBeInTheDocument()
  expect(within(row()).getByRole('img', { name: /фото кап промтеп/i })).toHaveAttribute(
    'src',
    original,
  )
})

test('admin marks a place as recommended and the list shows yes', async () => {
  const user = userEvent.setup()
  await renderAuthed('/places')

  await user.click(await screen.findByRole('button', { name: /добавить место/i }))
  const dialog = await screen.findByRole('dialog')
  await user.type(within(dialog).getByLabelText(/название/i), 'Мыс Промтеп')
  await user.selectOptions(within(dialog).getByLabelText(/категория/i), 'beach')
  await user.type(
    within(dialog).getByLabelText(/ссылка/i),
    'https://www.google.com/maps/place/Promthep/@7.76,98.30,17z',
  )
  await user.click(within(dialog).getByRole('button', { name: /сохранить/i }))

  const row = () => screen.getByText('Мыс Промтеп').closest('tr')!
  expect(row()).toHaveTextContent('нет')

  await user.click(within(row()).getByRole('button', { name: /изменить/i }))
  const edit = await screen.findByRole('dialog', { name: /изменить место/i })
  await user.selectOptions(within(edit).getByLabelText(/майк рекомендует/i), 'да')
  await user.click(within(edit).getByRole('button', { name: /сохранить/i }))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(row()).not.toHaveTextContent('нет')
  expect(row()).toHaveTextContent('да')
})
