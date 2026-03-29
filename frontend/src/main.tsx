import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router'
import './index.css'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { LabelingPage } from './pages/LabelingPage'
import { AdminDashboardPage } from './pages/AdminDashboardPage'
import { AdminProjectDetailPage } from './pages/AdminProjectDetailPage'
import { ProtectedRoute } from './components/ProtectedRoute'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute requiredRole="labeler">
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/project/:projectId"
          element={
            <ProtectedRoute requiredRole="labeler">
              <LabelingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/project/:projectId"
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminProjectDetailPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
