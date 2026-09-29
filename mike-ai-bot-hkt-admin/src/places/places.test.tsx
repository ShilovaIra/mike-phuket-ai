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
