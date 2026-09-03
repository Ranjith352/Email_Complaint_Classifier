import React, { useState, useEffect } from 'react';
import { Search, Filter, Plus, ArrowUpRight, CheckCircle, RefreshCw } from 'lucide-react';
import { getComplaints } from '../api/complaints';
import UrgencyBadge from '../components/UrgencyBadge';
import DepartmentBadge from '../components/DepartmentBadge';
import ComplaintDetailModal from '../components/ComplaintDetailModal';
import NewComplaintModal from '../components/NewComplaintModal';

export default function ComplaintsPage() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedUrgency, setSelectedUrgency] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  
  const [activeComplaint, setActiveComplaint] = useState(null);
  const [showNewModal, setShowNewModal] = useState(false);

  useEffect(() => {
    fetchComplaints();
  }, [search, selectedDept, selectedUrgency, selectedStatus]);

  const fetchComplaints = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (selectedDept) params.department = selectedDept;
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

      {/* Filters Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800/80 space-y-3">
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
      </div>

      {/* Complaints Table */}
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
                    <p className="font-semibold text-white truncate">{c.title}</p>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">{c.sender_email} · {c.description?.slice(0, 70)}...</p>
                  </td>
                  <td className="py-3 px-4"><DepartmentBadge department={c.department} /></td>
                  <td className="py-3 px-4"><UrgencyBadge urgency={c.urgency} /></td>
                  <td className="py-3 px-4 font-mono text-emerald-400 font-bold">
                    {Math.round(c.confidence * 100)}%
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
