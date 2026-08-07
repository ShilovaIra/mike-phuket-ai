import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from './auth/LoginPage'
import { RequireAuth } from './auth/RequireAuth'
import { PartnersPage } from './partners/PartnersPage'
import { StatsPage } from './stats/StatsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/partners" element={<PartnersPage />} />
        <Route path="/" element={<Navigate to="/stats" replace />} />
      </Route>
    </Routes>
  )
}
