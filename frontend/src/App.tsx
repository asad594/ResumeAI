import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './lib/auth'
import LoginPage from './pages/Login'
import RegisterPage from './pages/Register'
import DashboardLayout from './pages/DashboardLayout'
import DashboardPage from './pages/Dashboard'
import AnalyzePage from './pages/Analyze'
import HistoryPage from './pages/History'
import ProfilePage from './pages/Profile'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen bg-[#0F172A] flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#3B82F6]"></div></div>
  if (!user) return <Navigate to="/login" />
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" toastOptions={{ style: { background: '#1E293B', color: '#F8FAFC', border: '1px solid #334155', borderRadius: '12px' } }} />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="analyze" element={<AnalyzePage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="profile" element={<ProfilePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
