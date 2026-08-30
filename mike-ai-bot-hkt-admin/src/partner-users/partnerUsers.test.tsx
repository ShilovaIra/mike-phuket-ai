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
  expect(await screen.findByText('shop@example.com')).toBeInTheDocument()
  expect(screen.getByText('shop@example.com').closest('tr')).toHaveTextContent('Money Shop')
})
