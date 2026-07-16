import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import api from './api'

interface User { id: number; email: string; username: string; full_name: string | null }
interface AuthCtx { user: User | null; loading: boolean; login: (e: string, p: string) => Promise<void>; register: (e: string, u: string, p: string) => Promise<void>; logout: () => void }

const AuthContext = createContext<AuthCtx>({} as AuthCtx)
export const useAuth = () => useContext(AuthContext)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { setLoading(false); return }
    api.get('/auth/me').then(r => setUser(r.data)).catch(() => localStorage.removeItem('token')).finally(() => setLoading(false))
  }, [])

  const login = async (email: string, password: string) => {
    const r = await api.post('/auth/login', { email, password })
    localStorage.setItem('token', r.data.access_token)
    setUser(r.data.user)
  }

  const register = async (email: string, username: string, password: string) => {
    const r = await api.post('/auth/register', { email, username, password, full_name: username })
    localStorage.setItem('token', r.data.access_token)
    setUser(r.data.user)
  }

  const logout = () => { localStorage.removeItem('token'); setUser(null); window.location.href = '/login' }

  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>
}
