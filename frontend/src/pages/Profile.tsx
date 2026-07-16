import { useState } from 'react'
import { useAuth } from '../lib/auth'
import { User, Mail, AtSign, Save, Loader2 } from 'lucide-react'
import api from '../lib/api'
import toast from 'react-hot-toast'

export default function ProfilePage() {
  const { user } = useAuth()
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [username, setUsername] = useState(user?.username || '')
  const [saving, setSaving] = useState(false)

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true)
    try { await api.put('/auth/me', { full_name: fullName, username }); toast.success('Updated!') } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') } finally { setSaving(false) }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div><h1 className="text-2xl font-bold text-gray-100 mb-1">Profile</h1><p className="text-gray-400 text-sm">Manage your account</p></div>
      <div className="p-6 rounded-xl bg-[#1E293B] border border-gray-800">
        <div className="flex items-center gap-4">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#3B82F6] to-[#60A5FA] flex items-center justify-center text-white text-2xl font-bold">{user?.full_name?.[0] || user?.username?.[0] || 'U'}</div>
          <div><p className="font-semibold text-gray-100">{user?.full_name || user?.username}</p><p className="text-sm text-gray-400">{user?.email}</p></div>
        </div>
      </div>
      <div className="p-6 rounded-xl bg-[#1E293B] border border-gray-800">
        <h3 className="text-lg font-semibold text-gray-100 mb-4">Edit Profile</h3>
        <form onSubmit={handleUpdate} className="space-y-4">
          <div><label className="text-sm font-medium text-gray-300 mb-1 block">Full Name</label><div className="relative"><User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" /><input value={fullName} onChange={e => setFullName(e.target.value)} className="w-full h-10 rounded-xl border border-gray-700 bg-[#1E293B] pl-10 pr-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]" /></div></div>
          <div><label className="text-sm font-medium text-gray-300 mb-1 block">Username</label><div className="relative"><AtSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" /><input value={username} onChange={e => setUsername(e.target.value)} className="w-full h-10 rounded-xl border border-gray-700 bg-[#1E293B] pl-10 pr-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]" /></div></div>
          <div><label className="text-sm font-medium text-gray-300 mb-1 block">Email</label><div className="relative"><Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" /><input value={user?.email || ''} disabled className="w-full h-10 rounded-xl border border-gray-700 bg-[#1E293B] pl-10 pr-3 py-2 text-sm text-gray-500" /></div></div>
          <div className="flex justify-end"><button type="submit" disabled={saving} className="px-4 py-2 rounded-xl bg-[#3B82F6] text-white text-sm font-medium hover:bg-[#2563EB] transition-all flex items-center disabled:opacity-50 cursor-pointer">{saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />} Save Changes</button></div>
        </form>
      </div>
    </div>
  )
}
