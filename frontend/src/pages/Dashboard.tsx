import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileSearch, TrendingUp, Clock, BarChart3, Sparkles, ArrowRight } from 'lucide-react'
import api from '../lib/api'

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<any>(null)
  const [recent, setRecent] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/analysis/analytics').catch(() => ({ data: null })),
      api.get('/analysis/?page=1&per_page=5').catch(() => ({ data: { analyses: [] } }))
    ]).then(([a, h]) => { setAnalytics(a.data); setRecent(h.data?.analyses || []) }).finally(() => setLoading(false))
  }, [])

  const cards = [
    { title: 'Total Analyses', value: analytics?.total_analyses || 0, icon: FileSearch, color: 'text-[#60A5FA]', bg: 'bg-[#3B82F6]/10' },
    { title: 'Avg ATS Score', value: `${analytics?.average_ats_score || 0}%`, icon: TrendingUp, color: 'text-[#22C55E]', bg: 'bg-[#22C55E]/10' },
    { title: 'This Week', value: analytics?.weekly_activity?.reduce((a: number, b: any) => a + b.count, 0) || 0, icon: Clock, color: 'text-[#60A5FA]', bg: 'bg-[#60A5FA]/10' },
    { title: 'Top Skills', value: analytics?.most_common_skills?.length || 0, icon: BarChart3, color: 'text-[#EAB308]', bg: 'bg-[#EAB308]/10' },
  ]

  if (loading) return <div className="space-y-6">{[1,2,3,4].map(i => <div key={i} className="h-32 rounded-xl bg-[#1E293B] animate-pulse" />)}</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100 mb-1">Dashboard</h1>
        <p className="text-gray-400 text-sm">Welcome back! Here's your resume analysis overview.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c, i) => (
          <div key={i} className="p-5 rounded-xl bg-[#1E293B] border border-gray-800 hover:border-[#3B82F6]/30 transition-all">
            <div className="flex items-center justify-between">
              <div><p className="text-sm text-gray-400 mb-1">{c.title}</p><p className="text-2xl font-bold text-gray-100">{c.value}</p></div>
              <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center`}><c.icon className={`w-5 h-5 ${c.color}`} /></div>
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-xl bg-[#1E293B] border border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-100">Recent Analyses</h2>
            <Link to="/history" className="text-sm text-[#60A5FA] hover:text-[#3B82F6] flex items-center gap-1">View All <ArrowRight className="w-4 h-4" /></Link>
          </div>
          {recent.length === 0 ? (
            <div className="text-center py-12">
              <FileSearch className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 mb-4">No analyses yet</p>
              <Link to="/analyze" className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#3B82F6] text-white text-sm font-medium hover:bg-[#2563EB] transition-all"><Sparkles className="w-4 h-4" /> Analyze Your First Resume</Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recent.map((a: any) => (
                <div key={a.id} className="flex items-center justify-between p-3 rounded-xl bg-[#0F172A]/50 hover:bg-[#263548] transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[#3B82F6]/10 flex items-center justify-center"><FileSearch className="w-5 h-5 text-[#60A5FA]" /></div>
                    <div><p className="text-sm font-medium text-gray-200">Analysis #{a.id}</p><p className="text-xs text-gray-500">{new Date(a.created_at).toLocaleDateString()}</p></div>
                  </div>
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${a.ats_score >= 60 ? 'bg-[#22C55E]/20 text-[#22C55E]' : 'bg-[#EAB308]/20 text-[#EAB308]'}`}>ATS: {a.ats_score || 0}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="p-6 rounded-xl bg-[#1E293B] border border-gray-800">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link to="/analyze" className="block w-full px-4 py-2.5 rounded-xl border border-gray-700 text-sm text-gray-300 hover:bg-[#263548] transition-all text-left"><FileSearch className="w-4 h-4 inline mr-2" /> Analyze Resume</Link>
            <Link to="/history" className="block w-full px-4 py-2.5 rounded-xl border border-gray-700 text-sm text-gray-300 hover:bg-[#263548] transition-all text-left"><Clock className="w-4 h-4 inline mr-2" /> View History</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
