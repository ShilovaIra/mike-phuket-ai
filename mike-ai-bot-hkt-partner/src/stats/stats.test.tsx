import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { authApi } from '../auth/authApi'

test('stats page shows all-time and last 30 days totals', async () => {
  await authApi.login({ email: 'shop@example.com', password: 'shop-secret' })
  render(
    <MemoryRouter initialEntries={['/stats']}>
      <App />
    </MemoryRouter>,
  )

  expect(await screen.findByText('Показы (всё время)')).toBeInTheDocument()
  expect(screen.getByText('Переходы (всё время)')).toBeInTheDocument()
  expect(screen.getByText('Показы (30 дней)')).toBeInTheDocument()
  expect(screen.getByText('10')).toBeInTheDocument()
  expect(screen.getByText('5')).toBeInTheDocument()
})
