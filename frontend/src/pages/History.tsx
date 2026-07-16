import { useEffect, useState } from 'react'
import { History as HistoryIcon, Trash2, Search, FileText, Loader2 } from 'lucide-react'
import api from '../lib/api'
import toast from 'react-hot-toast'

export default function HistoryPage() {
  const [analyses, setAnalyses] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [deleting, setDeleting] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    api.get(`/analysis/?page=${page}&per_page=10`).then(r => { setAnalyses(r.data.analyses); setTotal(r.data.total) }).catch(() => toast.error('Failed to load')).finally(() => setLoading(false))
  }, [page])

  const handleDelete = async (id: number) => {
    setDeleting(id)
    try { await api.delete(`/analysis/${id}`); setAnalyses(p => p.filter(a => a.id !== id)); setTotal(p => p - 1); toast.success('Deleted') } catch { toast.error('Failed') } finally { setDeleting(null) }
  }

  const filtered = analyses.filter(a => !search || a.id.toString().includes(search) || new Date(a.created_at).toLocaleDateString().includes(search))

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold text-gray-100 mb-1">Analysis History</h1><p className="text-gray-400 text-sm">View your past resume analyses</p></div>
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md"><Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" /><input placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} className="w-full h-10 rounded-xl border border-gray-700 bg-[#1E293B] pl-10 pr-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]" /></div>
        <p className="text-sm text-gray-400">{total} total</p>
      </div>
      {loading ? <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 text-[#3B82F6] animate-spin" /></div> :
        filtered.length === 0 ? <div className="p-16 text-center rounded-xl bg-[#1E293B] border border-gray-800"><HistoryIcon className="w-12 h-12 text-gray-600 mx-auto mb-4" /><p className="text-gray-400">No analyses found</p></div> :
          <>
            <div className="space-y-3">
              {filtered.map((a: any) => (
                <div key={a.id} className="flex items-center justify-between p-4 rounded-xl bg-[#1E293B] border border-gray-800 hover:border-[#3B82F6]/30 transition-all">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-[#3B82F6]/10 flex items-center justify-center"><FileText className="w-5 h-5 text-[#60A5FA]" /></div>
                    <div><p className="text-sm font-medium text-gray-200">Analysis #{a.id}</p><p className="text-xs text-gray-500">Resume #{a.resume_id} &middot; {new Date(a.created_at).toLocaleDateString()}</p></div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${a.ats_score >= 60 ? 'bg-[#22C55E]/20 text-[#22C55E]' : 'bg-[#EAB308]/20 text-[#EAB308]'}`}>ATS: {a.ats_score || 0}%</span>
                    <button onClick={() => handleDelete(a.id)} disabled={deleting === a.id} className="p-2 rounded-lg hover:bg-[#EF4444]/10 text-gray-400 hover:text-[#EF4444] cursor-pointer">{deleting === a.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}</button>
                  </div>
                </div>
              ))}
            </div>
            {Math.ceil(total / 10) > 1 && (
              <div className="flex items-center justify-center gap-2">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1.5 rounded-lg border border-gray-700 text-sm text-gray-300 hover:bg-[#263548] disabled:opacity-50 cursor-pointer">Prev</button>
                <span className="text-sm text-gray-400">Page {page} of {Math.ceil(total / 10)}</span>
                <button onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil(total / 10)} className="px-3 py-1.5 rounded-lg border border-gray-700 text-sm text-gray-300 hover:bg-[#263548] disabled:opacity-50 cursor-pointer">Next</button>
              </div>
            )}
          </>
      }
    </div>
  )
}
