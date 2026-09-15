import React, { useState, useEffect } from 'react';
import { RefreshCw, Plus, Sparkles, HelpCircle, Layers, ArrowUpRight } from 'lucide-react';
import { getComplaints, semanticSearchComplaints } from '../api/complaints';
import { getDepartments } from '../api/departments';
import { getTeams } from '../api/teams';
import { getAgents } from '../api/agents';
import ComplaintTable from '../components/ComplaintTable';
import ComplaintDetailsPanel from '../components/ComplaintDetailsPanel';
import NewComplaintModal from '../components/NewComplaintModal';
import DepartmentBadge from '../components/DepartmentBadge';

export default function ComplaintsPage() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [departments, setDepartments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [agents, setAgents] = useState([]);
  
  // Active selected complaint displayed UNDER the table
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);
  const [selectedComplaint, setSelectedComplaint] = useState(null);

  // Search modes: 'standard' or 'semantic'
  const [searchMode, setSearchMode] = useState('standard');
  const [semanticQuery, setSemanticQuery] = useState('');
  const [semanticResults, setSemanticResults] = useState([]);
  const [semanticLoading, setSemanticLoading] = useState(false);

  // New Complaint Modal
  const [showNewModal, setShowNewModal] = useState(false);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [compData, deptData, teamData, agentData] = await Promise.allSettled([
        getComplaints(),
        getDepartments(),
        getTeams(),
        getAgents()
      ]);

      if (compData.status === 'fulfilled') {
        setComplaints(compData.value || []);
      }
      if (deptData.status === 'fulfilled') {
        setDepartments(deptData.value || []);
      }
      if (teamData.status === 'fulfilled') {
        setTeams(teamData.value || []);
      }
      if (agentData.status === 'fulfilled') {
        setAgents(agentData.value || []);
      }
    } catch (err) {
      console.error('Failed to load initial complaints data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchComplaints = async () => {
    setLoading(true);
    try {
      const data = await getComplaints();
      setComplaints(data || []);
      // If a complaint was selected, refresh it
      if (selectedComplaintId) {
        const updated = (data || []).find((c) => c.id === selectedComplaintId);
        if (updated) setSelectedComplaint(updated);
      }
    } catch (err) {
      console.error('Failed to refresh complaints:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectComplaint = (complaint) => {
    setSelectedComplaintId(complaint.id);
    setSelectedComplaint(complaint);
    // Smooth scroll down to details panel
    setTimeout(() => {
      const detailsEl = document.getElementById('complaint-details-container');
      if (detailsEl) {
        detailsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  };

  const handleCloseDetails = () => {
    setSelectedComplaintId(null);
    setSelectedComplaint(null);
  };

  const handleComplaintUpdated = (updated) => {
    fetchComplaints();
    if (updated && updated.id === selectedComplaintId) {
      setSelectedComplaint(updated);
    }
  };

  const handleSemanticSearch = async (queryText = semanticQuery) => {
    const q = queryText || semanticQuery;
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
    <div className="space-y-8 animate-fade-in pb-16">
      {/* Top Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-black text-white tracking-tight">Complaints Operations Center</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-brand-500/10 text-brand-400 border border-brand-500/30">
              Enterprise Hub
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            End-to-end complaint triage, multi-dimensional filtering, atomic actions, SLA tracking, and AI response drafting.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Mode Switcher */}
          <div className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl">
            <button
              onClick={() => setSearchMode('standard')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                searchMode === 'standard'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Table View
            </button>
            <button
              onClick={() => setSearchMode('semantic')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                searchMode === 'semantic'
                  ? 'bg-gradient-to-r from-purple-600 to-brand-600 text-white shadow-md'
                  : 'text-purple-300 hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Semantic Search</span>
            </button>
          </div>

          <button
            onClick={fetchComplaints}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh Complaints"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => setShowNewModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20 transition-all hover:scale-[1.02]"
          >
            <Plus className="w-4 h-4" />
            <span>Submit Ticket</span>
          </button>
        </div>
      </div>

      {/* Semantic Search Bar & Results if active */}
      {searchMode === 'semantic' && (
        <div className="glass-panel p-5 rounded-2xl border border-purple-500/30 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-purple-500/20 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-purple-300">
                AI Semantic Vector Search
              </h3>
            </div>
            <span className="text-[11px] text-slate-400">
              Matches conceptual queries against vector embeddings even without exact keyword overlap
            </span>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Sparkles className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-purple-400" />
                <input
                  type="text"
                  value={semanticQuery}
                  onChange={(e) => setSemanticQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSemanticSearch();
                  }}
                  placeholder="Ask in natural language: e.g., 'Money was deducted twice', 'cannot connect to server', 'charge disputed'..."
                  className="w-full bg-slate-950/80 border border-purple-500/40 focus:border-purple-500 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none ring-1 ring-purple-500/20"
                />
              </div>
              <button
                onClick={() => handleSemanticSearch()}
                disabled={semanticLoading || !semanticQuery.trim()}
                className="px-5 py-2.5 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white flex items-center gap-1.5 shadow-lg shadow-purple-600/20 disabled:opacity-50 transition-all"
              >
                <Sparkles className={`w-3.5 h-3.5 ${semanticLoading ? 'animate-spin' : ''}`} />
                <span>{semanticLoading ? 'Searching...' : 'Vector Search'}</span>
              </button>
            </div>

            {/* Example Queries */}
            <div className="flex items-center gap-2 flex-wrap text-[11px] text-slate-400">
              <span className="font-semibold text-slate-500">Quick Prompts:</span>
              {[
                'Money was deducted twice.',
                'I was charged two times for the same transaction.',
                'My account has been locked.',
                'Refund not received after cancellation.',
                'System crashes during authentication.'
              ].map((ex) => (
                <button
                  key={ex}
                  onClick={() => {
                    setSemanticQuery(ex);
                    handleSemanticSearch(ex);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-purple-950/50 text-slate-300 hover:text-purple-300 border border-slate-800 hover:border-purple-600/40 transition-colors"
                >
                  "{ex}"
                </button>
              ))}
            </div>
          </div>

          {/* Semantic Results Preview */}
          <div className="overflow-x-auto rounded-xl border border-slate-800/80 mt-4">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/70 text-slate-400">
                  <th className="py-3 px-4 font-semibold">Ticket ID</th>
                  <th className="py-3 px-4 font-semibold">Subject & Preview</th>
                  <th className="py-3 px-4 font-semibold">Category</th>
                  <th className="py-3 px-4 font-semibold">Semantic Match</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {semanticResults.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => handleSelectComplaint(r)}
                    className="hover:bg-purple-950/20 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-bold text-slate-300">{r.ticket_number}</td>
                    <td className="py-3 px-4 max-w-md">
                      <p className="font-semibold text-white truncate">{r.subject || 'Complaint'}</p>
                      <p className="text-[11px] text-slate-400 line-clamp-1">{r.description || r.body}</p>
                    </td>
                    <td className="py-3 px-4">
                      <DepartmentBadge department={r.category || r.department_name} />
                    </td>
                    <td className="py-3 px-4 font-mono">
                      <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold border ${
                        r.similarity_score >= 0.85
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                          : r.similarity_score >= 0.65
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                          : 'bg-slate-800 text-slate-300 border-slate-700'
                      }`}>
                        {Math.round(r.similarity_score * 100)}% Match
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                        {r.status || 'OPEN'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectComplaint(r);
                        }}
                        className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-purple-900/40 hover:bg-purple-800/60 text-purple-200 font-semibold border border-purple-700/50"
                      >
                        <span>View Details</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {semanticResults.length === 0 && !semanticLoading && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      {semanticQuery ? 'No matching complaints found.' : 'Submit a query or click a prompt above.'}
                    </td>
                  </tr>
                )}
                {semanticLoading && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-purple-400 font-mono animate-pulse">
                      Computing dense vector similarity across database...
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 1. PROFESSIONAL COMPLAINT TABLE (12 Columns, 8 Filters, Sort, Search, Pagination) */}
      <ComplaintTable
        complaints={complaints}
        loading={loading}
        selectedComplaintId={selectedComplaintId}
        onSelectComplaint={handleSelectComplaint}
        departments={departments}
        teams={teams}
        onRefresh={fetchComplaints}
      />

      {/* 2. COMPLAINT DETAILS VIEW UNDER IT (20 Display Elements, 14 Actions, Response Studio) */}
      <div id="complaint-details-container">
        {selectedComplaint ? (
          <div className="pt-4 border-t border-slate-800/80">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-brand-500 animate-pulse" />
                <h3 className="text-lg font-bold text-white tracking-tight">
                  Selected Ticket Telemetry & Action Suite
                </h3>
              </div>
              <span className="text-xs text-slate-400">
                Ticket: <strong className="text-white font-mono">{selectedComplaint.ticket_number}</strong>
              </span>
            </div>

            <ComplaintDetailsPanel
              complaintId={selectedComplaint.id}
              initialComplaint={selectedComplaint}
              onClose={handleCloseDetails}
              onUpdated={handleComplaintUpdated}
              departments={departments}
              teams={teams}
              agents={agents}
            />
          </div>
        ) : (
          <div className="p-8 rounded-2xl border border-dashed border-slate-800/80 text-center bg-slate-900/20">
            <Layers className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-400">
              No complaint selected
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Click "View Details" or any row above in the table to open comprehensive telemetry, SLA timeline, AI recommendation, and 14 triage actions directly underneath.
            </p>
          </div>
        )}
      </div>

      {/* New Complaint Modal */}
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
