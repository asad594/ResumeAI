import { useState, useRef } from 'react'
import { Upload, FileText, X, Loader2, Sparkles, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react'
import api from '../lib/api'
import toast from 'react-hot-toast'

function CircularScore({ score }: { score: number }) {
  const r = 70, c = 2 * Math.PI * r, offset = c - (score / 100) * c
  const color = score >= 80 ? '#22C55E' : score >= 60 ? '#EAB308' : '#EF4444'
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={160} height={160} className="-rotate-90">
        <circle cx={80} cy={80} r={r} fill="none" stroke="#334155" strokeWidth="8" />
        <circle cx={80} cy={80} r={r} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" strokeDasharray={c} strokeDashoffset={offset} className="transition-all duration-1000" />
      </svg>
      <div className="absolute text-center">
        <p className="text-3xl font-bold" style={{ color }}>{Math.round(score)}</p>
        <p className="text-xs text-gray-400">out of 100</p>
      </div>
    </div>
  )
}

export default function AnalyzePage() {
  const [step, setStep] = useState<'upload' | 'details' | 'results'>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [resume, setResume] = useState<any>(null)
  const [jobDesc, setJobDesc] = useState('')
  const [analysis, setAnalysis] = useState<any>(null)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (f: File) => {
    if (f.size > 10 * 1024 * 1024) { toast.error('Max 10MB'); return }
    setFile(f); setUploading(true)
    try {
      const fd = new FormData(); fd.append('file', f)
      const r = await api.post('/resumes/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setResume(r.data); toast.success('Resume uploaded!'); setStep('details')
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Upload failed') } finally { setUploading(false) }
  }

  const handleDrop = (e: React.DragEvent) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => { const f = e.target.files?.[0]; if (f) handleFile(f) }

  const handleAnalyze = async () => {
    if (!resume) return; setAnalyzing(true)
    try {
      const r = await api.post('/analysis/', { resume_id: resume.id, job_description: jobDesc || undefined })
      setAnalysis(r.data); setStep('results'); toast.success('Analysis complete!')
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Analysis failed') } finally { setAnalyzing(false) }
  }

  const reset = () => { setStep('upload'); setFile(null); setResume(null); setJobDesc(''); setAnalysis(null) }

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold text-gray-100 mb-1">Resume Analyzer</h1><p className="text-gray-400 text-sm">Upload your resume and get AI-powered insights</p></div>

      <div className="flex items-center gap-4">
        {(['upload', 'details', 'results'] as const).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step === s ? 'bg-[#3B82F6] text-white' : i < ['upload', 'details', 'results'].indexOf(step) ? 'bg-[#22C55E] text-white' : 'bg-gray-800 text-gray-500'}`}>
              {i < ['upload', 'details', 'results'].indexOf(step) ? <CheckCircle className="w-4 h-4" /> : i + 1}
            </div>
            <span className={`text-sm capitalize ${step === s ? 'text-gray-100' : 'text-gray-500'}`}>{s}</span>
            {i < 2 && <div className="w-12 h-px bg-gray-700 mx-2" />}
          </div>
        ))}
      </div>

      {step === 'upload' && (
        <div className="p-8 rounded-xl bg-[#1E293B] border border-gray-800">
          <input ref={inputRef} type="file" accept=".pdf,.docx" className="hidden" onChange={handleChange} />
          <div onDragOver={(e) => { e.preventDefault(); setDragOver(true) }} onDragLeave={() => setDragOver(false)} onDrop={handleDrop} onClick={() => inputRef.current?.click()} className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${dragOver ? 'border-[#3B82F6] bg-[#3B82F6]/5' : 'border-gray-700 hover:border-[#3B82F6]/50 hover:bg-[#3B82F6]/5'}`}>
            {uploading ? <div className="space-y-4"><Loader2 className="w-12 h-12 text-[#60A5FA] mx-auto animate-spin" /><p className="text-gray-300">Uploading...</p></div> :
              <><Upload className="w-12 h-12 text-gray-500 mx-auto mb-4" /><h3 className="text-lg font-semibold text-gray-200 mb-2">{dragOver ? 'Drop here' : 'Drag & drop your resume'}</h3><p className="text-gray-400 text-sm mb-4">or click to browse</p><div className="flex items-center justify-center gap-4 text-xs text-gray-500"><span>PDF</span><span>DOCX</span><span>Max 10MB</span></div></>}
          </div>
        </div>
      )}

      {step === 'details' && resume && (
        <div className="space-y-6">
          <div className="p-6 rounded-xl bg-[#1E293B] border border-gray-800">
            <div className="flex items-center justify-between p-4 rounded-xl bg-[#0F172A]/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-[#3B82F6]/10 flex items-center justify-center"><FileText className="w-5 h-5 text-[#60A5FA]" /></div>
                <div><p className="text-sm font-medium text-gray-200">{resume.filename}</p><p className="text-xs text-gray-500">Uploaded</p></div>
              </div>
              <button onClick={() => { setFile(null); setResume(null); setStep('upload') }} className="p-2 rounded-lg hover:bg-[#263548] cursor-pointer"><X className="w-4 h-4 text-gray-400" /></button>
            </div>
          </div>
          <div className="p-6 rounded-xl bg-[#1E293B] border border-gray-800">
            <h3 className="text-base font-semibold text-gray-100 mb-3">Job Description (Optional)</h3>
            <p className="text-sm text-gray-400 mb-3">Paste a job description to compare against</p>
            <textarea placeholder="Paste job description here..." value={jobDesc} onChange={e => setJobDesc(e.target.value)} rows={6} className="w-full rounded-xl border border-gray-700 bg-[#1E293B] px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-[#3B82F6] resize-none" />
          </div>
          <div className="flex justify-end gap-3">
            <button onClick={reset} className="px-4 py-2 rounded-xl border border-gray-700 text-sm text-gray-300 hover:bg-[#263548] cursor-pointer">Start Over</button>
            <button onClick={handleAnalyze} disabled={analyzing} className="px-6 py-2.5 rounded-xl bg-[#3B82F6] text-white text-sm font-medium hover:bg-[#2563EB] transition-all flex items-center disabled:opacity-50 cursor-pointer">
              {analyzing ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Analyzing...</> : <><Sparkles className="w-4 h-4 mr-2" /> Analyze Resume</>}
            </button>
          </div>
        </div>
      )}

      {step === 'results' && analysis && (
        <div className="space-y-6">
          <div className="p-6 rounded-xl bg-[#1E293B] border border-gray-800">
            <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center gap-2"><Sparkles className="w-5 h-5 text-[#60A5FA]" /> ATS Score</h3>
            <div className="flex flex-col md:flex-row items-center gap-8">
              <CircularScore score={analysis.ats_score || 0} />
              <div className="flex-1 grid grid-cols-2 md:grid-cols-3 gap-4 w-full">
                {analysis.ats_details && Object.entries(analysis.ats_details).filter(([k]) => k !== 'overall').map(([k, v]: any) => (
                  <div key={k} className="p-3 rounded-xl bg-[#0F172A]/50">
                    <p className="text-xs text-gray-500 mb-1 capitalize">{k}</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 rounded-full bg-gray-800"><div className={`h-2 rounded-full transition-all ${v >= 80 ? 'bg-[#22C55E]' : v >= 60 ? 'bg-[#EAB308]' : 'bg-[#EF4444]'}`} style={{ width: `${v}%` }} /></div>
                      <span className="text-sm font-medium text-gray-300">{Math.round(v)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { title: 'Matched Skills', skills: analysis.matched_skills, color: 'bg-[#22C55E]/20 text-[#22C55E] border-[#22C55E]/30', icon: CheckCircle },
              { title: 'Missing Skills', skills: analysis.missing_skills, color: 'bg-[#EF4444]/20 text-[#EF4444] border-[#EF4444]/30', icon: AlertCircle },
              { title: 'Partial Match', skills: analysis.partial_skills, color: 'bg-[#EAB308]/20 text-[#EAB308] border-[#EAB308]/30', icon: AlertCircle },
            ].map((section) => (
              <div key={section.title} className="p-5 rounded-xl bg-[#1E293B] border border-gray-800">
                <h4 className="text-base font-semibold text-gray-100 mb-3 flex items-center gap-2"><section.icon className="w-4 h-4" /> {section.title}</h4>
                <div className="flex flex-wrap gap-2">
                  {section.skills?.length ? section.skills.map((s: string) => <span key={s} className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${section.color}`}>{s}</span>) : <p className="text-sm text-gray-500">None</p>}
                </div>
              </div>
            ))}
          </div>

          <div className="p-6 rounded-xl bg-[#1E293B] border border-gray-800">
            <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center gap-2"><Sparkles className="w-5 h-5 text-[#60A5FA]" /> Suggestions</h3>
            <div className="space-y-3">
              {analysis.suggestions?.map((s: any, i: number) => (
                <div key={i} className="p-4 rounded-xl bg-[#0F172A]/50 border border-gray-800 hover:border-[#3B82F6]/30 transition-all">
                  <div className="flex items-start gap-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${s.severity === 'high' ? 'bg-[#EF4444]/20 text-[#EF4444]' : s.severity === 'medium' ? 'bg-[#EAB308]/20 text-[#EAB308]' : 'bg-gray-700 text-gray-300'}`}>{s.severity}</span>
                    <div className="flex-1"><h4 className="text-sm font-medium text-gray-200 mb-1">{s.title}</h4><p className="text-xs text-gray-400">{s.description}</p></div>
                    <span className="px-2 py-0.5 rounded text-xs text-gray-400 border border-gray-700">{s.category}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {analysis.job_match?.recommended_roles?.length > 0 && (
            <div className="p-6 rounded-xl bg-[#1E293B] border border-gray-800">
              <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center gap-2"><TrendingUp className="w-5 h-5 text-[#60A5FA]" /> Job Match</h3>
              <p className="text-sm text-gray-400 mb-4">Similarity: <span className="text-[#60A5FA] font-semibold">{analysis.job_match.similarity_score}%</span></p>
              <div className="space-y-3">
                {analysis.job_match.recommended_roles.map((r: any) => (
                  <div key={r.title} className="flex items-center justify-between p-3 rounded-xl bg-[#0F172A]/50">
                    <span className="text-sm font-medium text-gray-200">{r.title}</span>
                    <div className="flex items-center gap-3">
                      <div className="w-24 h-2 rounded-full bg-gray-800"><div className="h-2 rounded-full bg-[#3B82F6]" style={{ width: `${r.match}%` }} /></div>
                      <span className="text-sm font-medium text-gray-300 w-10 text-right">{r.match}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end">
            <button onClick={reset} className="px-4 py-2 rounded-xl border border-gray-700 text-sm text-gray-300 hover:bg-[#263548] cursor-pointer">Analyze Another Resume</button>
          </div>
        </div>
      )}
    </div>
  )
}
