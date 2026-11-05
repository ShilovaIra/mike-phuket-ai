import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { authApi } from '../auth/authApi'
import { seedBroadcasts } from '../test/mockBackend'

async function renderAuthed(path: string) {
  await authApi.login({ email: 'admin@example.com', password: 'admin123' })
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

test('admin can schedule a broadcast and see it in the list', async () => {
  const user = userEvent.setup()
  await renderAuthed('/broadcasts')

  await user.type(await screen.findByLabelText(/текст сообщения/i), 'Как вам Пхукет?')
  fireEvent.change(screen.getByLabelText(/дата/i), {
    target: { value: '2026-12-01T10:00' },
  })
  await user.click(screen.getByRole('button', { name: /сохранить/i }))

  expect(await screen.findByText('Как вам Пхукет?')).toBeInTheDocument()
})

test('a sent broadcast is grey and cannot be edited or deleted', async () => {
  seedBroadcasts([
    {
      id: 'sent-1',
      text: 'Уже ушло',
      scheduled_at: '2026-11-01T10:00:00+07:00',
      status: 'sent',
      button_url: null,
      button_label: null,
    },
    {
      id: 'soon-1',
      text: 'Ещё впереди',
      scheduled_at: '2026-12-01T10:00:00+07:00',
      status: 'scheduled',
      button_url: null,
      button_label: null,
    },
  ])
  await renderAuthed('/broadcasts')

  const sent = (await screen.findByText('Уже ушло')).closest('li')
  expect(sent).toHaveClass('text-slate-400')
  expect(within(sent!).queryByRole('button', { name: /изменить/i })).not.toBeInTheDocument()
  expect(within(sent!).queryByRole('button', { name: /удалить/i })).not.toBeInTheDocument()

  const scheduled = screen.getByText('Ещё впереди').closest('li')
  expect(within(scheduled!).getByRole('button', { name: /изменить/i })).toBeInTheDocument()
  expect(within(scheduled!).getByRole('button', { name: /удалить/i })).toBeInTheDocument()
})

test('admin can delete a scheduled broadcast from the list', async () => {
  const user = userEvent.setup()
  seedBroadcasts([
    {
      id: 'soon-1',
      text: 'Ещё впереди',
      scheduled_at: '2026-12-01T10:00:00+07:00',
      status: 'scheduled',
      button_url: null,
      button_label: null,
    },
  ])
  await renderAuthed('/broadcasts')
  await user.click(await screen.findByRole('button', { name: /удалить/i }))
  expect(screen.queryByText('Ещё впереди')).not.toBeInTheDocument()
})

test('admin can edit a scheduled broadcast from the list', async () => {
  const user = userEvent.setup()
  seedBroadcasts([
    {
      id: 'soon-1',
      text: 'Ещё впереди',
      scheduled_at: '2026-12-01T10:00:00+07:00',
      status: 'scheduled',
      button_url: null,
      button_label: null,
    },
  ])
  await renderAuthed('/broadcasts')
  await user.click(await screen.findByRole('button', { name: /изменить/i }))
  const text = screen.getByLabelText(/текст сообщения/i)
  expect(text).toHaveValue('Ещё впереди')
  await user.clear(text)
  await user.type(text, 'Новый текст')
  await user.click(screen.getByRole('button', { name: /сохранить/i }))
  expect(await screen.findByText('Новый текст')).toBeInTheDocument()
  expect(screen.queryByText('Ещё впереди')).not.toBeInTheDocument()
})
