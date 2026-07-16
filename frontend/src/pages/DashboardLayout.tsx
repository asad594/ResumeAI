import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { LayoutDashboard, FileSearch, History, User, LogOut, Sparkles } from 'lucide-react'

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/analyze', label: 'Resume Analyzer', icon: FileSearch },
  { to: '/history', label: 'History', icon: History },
  { to: '/profile', label: 'Profile', icon: User },
]

export default function DashboardLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-[#0F172A] flex">
      <aside className="w-64 h-screen bg-[#1E293B] border-r border-gray-800 flex flex-col fixed left-0 top-0">
        <div className="p-4 border-b border-gray-800 flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#3B82F6] to-[#60A5FA] flex items-center justify-center"><Sparkles className="w-4 h-4 text-white" /></div>
          <span className="font-bold text-gray-100 text-lg">ResumeAI</span>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map(item => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${isActive ? 'bg-[#3B82F6]/15 text-[#60A5FA]' : 'text-gray-400 hover:text-gray-200 hover:bg-[#263548]'}`}>
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-gray-800">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#3B82F6] to-[#60A5FA] flex items-center justify-center text-white text-sm font-bold">{user?.username?.[0]?.toUpperCase()}</div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-200 truncate">{user?.full_name || user?.username}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button onClick={logout} className="w-full flex items-center gap-3 px-3 py-2 mt-1 rounded-xl text-sm text-gray-400 hover:text-[#EF4444] hover:bg-[#EF4444]/10 transition-all cursor-pointer">
            <LogOut className="w-5 h-5" /> Logout
          </button>
        </div>
      </aside>
      <div className="ml-64 flex-1">
        <header className="h-16 border-b border-gray-800 bg-[#1E293B]/50 backdrop-blur-xl flex items-center px-6 sticky top-0 z-40">
          <div />
        </header>
        <main className="p-6"><Outlet /></main>
      </div>
    </div>
  )
}
