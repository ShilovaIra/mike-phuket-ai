import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from './auth/LoginPage'
import { RequireAuth } from './auth/RequireAuth'
import { PartnerTypeFormPage } from './partner-types/PartnerTypeFormPage'
import { PartnerTypesPage } from './partner-types/PartnerTypesPage'
import { PartnerFormPage } from './partners/PartnerFormPage'
import { PartnersPage } from './partners/PartnersPage'
import { StatsPage } from './stats/StatsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/partners" element={<PartnersPage />} />
        <Route path="/partners/new" element={<PartnerFormPage mode="create" />} />
        <Route path="/partners/:id/edit" element={<PartnerFormPage mode="edit" />} />
        <Route path="/partner-types" element={<PartnerTypesPage />} />
        <Route path="/partner-types/new" element={<PartnerTypeFormPage mode="create" />} />
        <Route path="/partner-types/:slug/edit" element={<PartnerTypeFormPage mode="edit" />} />
        <Route path="/" element={<Navigate to="/stats" replace />} />
      </Route>
    </Routes>
  )
}
