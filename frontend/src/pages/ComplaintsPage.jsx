import React, { useState, useEffect } from 'react';
import { Search, Filter, Plus, ArrowUpRight, CheckCircle, RefreshCw, Sparkles, HelpCircle } from 'lucide-react';
import { getComplaints, semanticSearchComplaints } from '../api/complaints';
import UrgencyBadge from '../components/UrgencyBadge';
import DepartmentBadge from '../components/DepartmentBadge';
import ComplaintDetailModal from '../components/ComplaintDetailModal';
import NewComplaintModal from '../components/NewComplaintModal';

export default function ComplaintsPage() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [searchMode, setSearchMode] = useState('filter'); // 'filter' | 'semantic'
  const [semanticResults, setSemanticResults] = useState([]);
  const [semanticLoading, setSemanticLoading] = useState(false);
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedUrgency, setSelectedUrgency] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  
  const [activeComplaint, setActiveComplaint] = useState(null);
  const [showNewModal, setShowNewModal] = useState(false);

  useEffect(() => {
    if (searchMode === 'filter') {
      fetchComplaints();
    }
  }, [search, selectedDept, selectedUrgency, selectedStatus, searchMode]);

  const fetchComplaints = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (selectedDept) params.department_id = selectedDept;
      if (selectedUrgency) params.urgency = selectedUrgency;
      if (selectedStatus) params.status = selectedStatus;
      
      const data = await getComplaints(params);
      setComplaints(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSemanticSearch = async (queryText = search) => {
    const q = queryText || search;
    if (!q || !q.trim()) return;
    setSemanticLoading(true);
    try {
      const res = await semanticSearchComplaints(q.trim(), 15, 0.35);
      setSemanticResults(res.results || []);
    } catch (err) {
      console.error('Semantic search failed:', err);
    } finally {
      setSemanticLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tight">Complaints & Triage Explorer</h2>
          <p className="text-xs text-slate-400 mt-1">
            Browse, search, and manage all incoming customer complaints with AI-augmented routing.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchComplaints}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
            title="Refresh Complaints"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowNewModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20"
          >
            <Plus className="w-4 h-4" />
            <span>Submit Ticket</span>
          </button>
        </div>
      </div>

      {/* Filters & Semantic Search Bar */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4 shadow-xl">
        <div className="flex items-center justify-between flex-wrap gap-3 pb-2 border-b border-slate-800/60">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setSearchMode('filter');
                fetchComplaints();
              }}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                searchMode === 'filter'
                  ? 'bg-slate-800 text-white border border-slate-700 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Standard Filter
            </button>
            <button
              onClick={() => {
                setSearchMode('semantic');
                if (search) handleSemanticSearch(search);
              }}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                searchMode === 'semantic'
                  ? 'bg-gradient-to-r from-purple-600 to-brand-600 text-white shadow-lg shadow-purple-600/20'
                  : 'text-purple-300 hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Semantic Search (AI Embeddings)</span>
            </button>
          </div>

          {searchMode === 'semantic' && (
            <span className="text-[11px] text-purple-300/80 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-purple-400" />
              Powered by Sentence Transformers & pgvector
            </span>
          )}
        </div>

        {searchMode === 'filter' ? (
          <>
            <div className="flex items-center gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by ticket #, customer email, keyword, or issue details..."
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>

            {/* Filter Badges Row */}
            <div className="flex items-center gap-2 flex-wrap text-xs pt-1">
              <span className="text-slate-500 font-semibold text-[11px] uppercase mr-1 flex items-center gap-1">
                <Filter className="w-3 h-3" /> Dept:
              </span>
              {['', 'IT', 'Finance', 'Security', 'Support', 'Operations'].map((dept) => (
                <button
                  key={dept}
                  onClick={() => setSelectedDept(dept)}
                  className={`px-2.5 py-1 rounded-lg transition-all ${
                    selectedDept === dept
                      ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 font-bold'
                      : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200'
                  }`}
                >
                  {dept || 'All Departments'}
                </button>
              ))}

              <div className="h-4 w-px bg-slate-800 mx-1" />

              <span className="text-slate-500 font-semibold text-[11px] uppercase mr-1">Urgency:</span>
              {['', 'Critical', 'High', 'Medium', 'Low'].map((urg) => (
                <button
                  key={urg}
                  onClick={() => setSelectedUrgency(urg)}
                  className={`px-2.5 py-1 rounded-lg transition-all ${
                    selectedUrgency === urg
                      ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 font-bold'
                      : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200'
                  }`}
                >
                  {urg || 'All Urgencies'}
                </button>
              ))}

              <div className="h-4 w-px bg-slate-800 mx-1" />

              <span className="text-slate-500 font-semibold text-[11px] uppercase mr-1">Status:</span>
              {['', 'Open', 'In Progress', 'Resolved'].map((st) => (
                <button
                  key={st}
                  onClick={() => setSelectedStatus(st)}
                  className={`px-2.5 py-1 rounded-lg transition-all ${
                    selectedStatus === st
                      ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 font-bold'
                      : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200'
                  }`}
                >
                  {st || 'All Statuses'}
                </button>
              ))}
            </div>
          </>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Sparkles className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-purple-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSemanticSearch();
                  }}
                  placeholder="Ask in natural language: e.g., 'Money was deducted twice', 'charged two times', 'wifi dropped'..."
                  className="w-full bg-slate-950/80 border border-purple-500/40 focus:border-purple-500 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none ring-1 ring-purple-500/20"
                />
              </div>
              <button
                onClick={() => handleSemanticSearch()}
                disabled={semanticLoading || !search.trim()}
                className="px-5 py-2.5 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white flex items-center gap-1.5 shadow-lg shadow-purple-600/20 disabled:opacity-50"
              >
                <Sparkles className={`w-3.5 h-3.5 ${semanticLoading ? 'animate-spin' : ''}`} />
                <span>{semanticLoading ? 'Searching...' : 'Semantic Search'}</span>
              </button>
            </div>

            {/* Example Queries */}
            <div className="flex items-center gap-2 flex-wrap text-[11px] text-slate-400">
              <span className="font-semibold text-slate-500">Try Example Prompts:</span>
              {[
                'Money was deducted twice.',
                'I was charged two times for the same transaction.',
                'My account has been hacked.',
                'Refund not received after cancellation.',
                'The system keeps crashing when saving.'
              ].map((ex) => (
                <button
                  key={ex}
                  onClick={() => {
                    setSearch(ex);
                    handleSemanticSearch(ex);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-purple-950/50 text-slate-300 hover:text-purple-300 border border-slate-800 hover:border-purple-600/40 transition-colors"
                >
                  "{ex}"
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Semantic Search Results Table */}
      {searchMode === 'semantic' ? (
        <div className="glass-panel rounded-2xl border border-purple-500/20 overflow-hidden shadow-xl">
          <div className="p-4 bg-purple-950/20 border-b border-purple-500/20 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-purple-300">
                Semantic Match Results ({semanticResults.length})
              </h3>
            </div>
            <span className="text-[11px] text-slate-400">
              Matches complaints conceptually even when phrasing is completely different
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400">
                  <th className="py-3 px-4 font-semibold">Ticket</th>
                  <th className="py-3 px-4 font-semibold">Complaint Subject & Description</th>
                  <th className="py-3 px-4 font-semibold">Category</th>
                  <th className="py-3 px-4 font-semibold">Semantic Match Score</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {semanticResults.map((r) => (
                  <tr key={r.id} className="hover:bg-purple-950/15 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-300">{r.ticket_number}</td>
                    <td className="py-3 px-4 max-w-md">
                      <p className="font-semibold text-white truncate">{r.subject || 'Complaint Inquiry'}</p>
                      <p className="text-[11px] text-slate-400 line-clamp-2 mt-0.5 leading-relaxed">
                        {r.description || 'No description preview available.'}
                      </p>
                    </td>
                    <td className="py-3 px-4">
                      <DepartmentBadge department={r.category} />
                    </td>
                    <td className="py-3 px-4 font-mono">
                      <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold border ${
                        r.similarity_score >= 0.85
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-sm'
                          : r.similarity_score >= 0.65
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                          : 'bg-slate-800 text-slate-300 border-slate-700'
                      }`}>
                        {Math.round(r.similarity_score * 100)}% Match
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold border bg-slate-850 text-slate-300 border-slate-700">
                        {r.status || 'OPEN'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setActiveComplaint(r)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-purple-900/40 hover:bg-purple-800/60 text-purple-200 font-semibold border border-purple-700/50 transition-all"
                      >
                        <span>Inspect</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {semanticResults.length === 0 && !semanticLoading && (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-500">
                      {search ? 'No semantically similar complaints found for your query.' : 'Type a query or select an example above to execute semantic search.'}
                    </td>
                  </tr>
                )}
                {semanticLoading && (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-purple-400 font-mono animate-pulse">
                      Computing dense vector similarity across complaints database...
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Standard Complaints Table */
        <div className="glass-panel rounded-2xl border border-slate-800/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400">
                  <th className="py-3 px-4 font-semibold">Ticket ID</th>
                  <th className="py-3 px-4 font-semibold">Subject & Customer Details</th>
                  <th className="py-3 px-4 font-semibold">Assigned Dept</th>
                  <th className="py-3 px-4 font-semibold">Urgency</th>
                  <th className="py-3 px-4 font-semibold">NLP Confidence</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {complaints.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-300">{c.ticket_number}</td>
                    <td className="py-3 px-4 max-w-sm md:max-w-md">
                      <p className="font-semibold text-white truncate">{c.subject || c.title}</p>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">{c.customer_email || c.sender_email} · {(c.body || c.description)?.slice(0, 70)}...</p>
                    </td>
                    <td className="py-3 px-4"><DepartmentBadge department={c.category || c.department} /></td>
                    <td className="py-3 px-4"><UrgencyBadge urgency={c.urgency} /></td>
                    <td className="py-3 px-4 font-mono text-emerald-400 font-bold">
                      {Math.round((c.ai_confidence || c.confidence || 0.88) * 100)}%
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                        c.status === 'Resolved'
                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                          : 'bg-blue-500/10 text-blue-300 border-blue-500/30'
                      }`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setActiveComplaint(c)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-850 hover:bg-slate-800 text-brand-300 font-semibold border border-slate-700/80 transition-all hover:border-brand-500/50"
                      >
                        <span>AI Triage</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {complaints.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-slate-500">
                      {loading ? 'Loading complaints database...' : 'No complaints matched your active filter criteria.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}


      {activeComplaint && (
        <ComplaintDetailModal
          complaint={activeComplaint}
          onClose={() => setActiveComplaint(null)}
          onUpdated={() => {
            fetchComplaints();
            setActiveComplaint(null);
          }}
        />
      )}

      {showNewModal && (
        <NewComplaintModal
          onClose={() => setShowNewModal(false)}
          onCreated={() => {
            fetchComplaints();
            setShowNewModal(false);
          }}
        />
      )}
    </div>
  );
}
