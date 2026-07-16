import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { Sparkles, Mail, Lock, Eye, EyeOff, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(email, password)
      toast.success('Welcome back!')
      nav('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid credentials')
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-[#0F172A] flex items-center justify-center p-6">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[#3B82F6]/10 via-transparent to-transparent" />
      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#3B82F6] to-[#60A5FA] flex items-center justify-center"><Sparkles className="w-5 h-5 text-white" /></div>
            <span className="font-bold text-xl text-gray-100">ResumeAI</span>
          </Link>
          <h1 className="text-2xl font-bold text-gray-100 mb-2">Welcome back</h1>
          <p className="text-gray-400">Sign in to your account</p>
        </div>
        <div className="p-8 rounded-2xl bg-[#1E293B] border border-gray-800">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-300 mb-1 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} className="w-full h-10 rounded-xl border border-gray-700 bg-[#1E293B] pl-10 pr-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]" required />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-300 mb-1 block">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input type={show ? 'text' : 'password'} placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="w-full h-10 rounded-xl border border-gray-700 bg-[#1E293B] pl-10 pr-10 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]" required />
                <button type="button" onClick={() => setShow(!show)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 cursor-pointer">{show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}</button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="w-full h-11 rounded-xl bg-[#3B82F6] text-white font-medium hover:bg-[#2563EB] transition-all duration-200 flex items-center justify-center disabled:opacity-50 cursor-pointer">
              {loading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Signing in...</> : 'Sign In'}
            </button>
          </form>
        </div>
        <p className="text-center mt-6 text-sm text-gray-400">Don't have an account? <Link to="/register" className="text-[#60A5FA] hover:text-[#3B82F6] font-medium">Sign up free</Link></p>
      </div>
    </div>
  )
}
