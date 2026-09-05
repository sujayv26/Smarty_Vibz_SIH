import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './features/auth/AuthContext'
import { Layout } from './components/Layout'
import { Login } from './features/auth/Login'
import { Dashboard } from './features/dashboard/Dashboard'
import { ScheduleView } from './features/schedule/ScheduleView'
import { PlannerQueue } from './features/planner/PlannerQueue'
import { TimeAgent } from './features/agent/TimeAgent'
import { InboundChannels } from './features/inbound/InboundChannels'
import { Insights } from './features/insights/Insights'
import { RiskWatchlist } from './features/risk/RiskWatchlist'
import { BIMViewer } from './features/bim/BIMViewer'
import { AdminPanel } from './features/admin/AdminPanel'
import { Settings } from './features/settings/Settings'

function ProtectedRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles?: string[] }) {
  const { isAuthenticated, isLoading, user, hasRole } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bgApp">
        <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && user && !hasRole(allowedRoles as any)) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bgApp">
        <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="schedule" element={<ScheduleView />} />
        <Route path="planner-queue" element={<PlannerQueue />} />
        <Route path="time-agent" element={<TimeAgent />} />
        <Route path="inbound" element={<InboundChannels />} />
        <Route path="insights" element={<Insights />} />
        <Route path="risk" element={<RiskWatchlist />} />
        <Route path="bim" element={<BIMViewer />} />
        <Route
          path="admin"
          element={
            <ProtectedRoute allowedRoles={['SYSTEM_ADMIN', 'CONTRACTOR_ADMIN']}>
              <AdminPanel />
            </ProtectedRoute>
          }
        />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}