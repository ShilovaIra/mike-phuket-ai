import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from './auth/LoginPage'
import { RequireAuth } from './auth/RequireAuth'
import { PartnerUsersPage } from './partner-users/PartnerUsersPage'
import { PartnerTypesPage } from './partner-types/PartnerTypesPage'
import { PlaceCategoriesPage } from './place-categories/PlaceCategoriesPage'
import { PlacesPage } from './places/PlacesPage'
import { PartnersPage } from './partners/PartnersPage'
import { StatsPage } from './stats/StatsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/partners" element={<PartnersPage />} />
        <Route path="/partner-types" element={<PartnerTypesPage />} />
        <Route path="/place-categories" element={<PlaceCategoriesPage />} />
        <Route path="/places" element={<PlacesPage />} />
        <Route path="/partner-users" element={<PartnerUsersPage />} />
        <Route path="/" element={<Navigate to="/stats" replace />} />
      </Route>
    </Routes>
  )
}

