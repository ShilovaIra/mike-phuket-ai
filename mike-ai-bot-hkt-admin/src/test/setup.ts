import '@testing-library/jest-dom/vitest'
import { installFetchMock, resetMockBackend } from './mockBackend'

beforeEach(() => {
  localStorage.clear()
  resetMockBackend()
  installFetchMock()
})
