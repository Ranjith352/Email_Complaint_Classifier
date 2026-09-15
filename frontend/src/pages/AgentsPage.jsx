import React, { useState, useEffect, useMemo } from 'react';
import { UserCheck, Shield, Activity, Mail, Search, Filter, RefreshCw, CheckCircle2 } from 'lucide-react';
import apiClient from '../api/client';
import { CardSkeleton } from '../components/LoadingSkeleton';
import EmptyState from '../components/EmptyState';

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDept, setSelectedDept] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [agentsRes, deptsRes] = await Promise.all([
        apiClient.get('/agents'),
        apiClient.get('/departments/').catch(() => ({ data: [] }))
      ]);
      const agentList = Array.isArray(agentsRes.data)
        ? agentsRes.data
        : agentsRes.data?.data || agentsRes.data?.agents || [];
      setAgents(agentList);
      setDepartments(Array.isArray(deptsRes.data) ? deptsRes.data : []);
    } catch (err) {
      console.error('Failed to load agents:', err);
      setAgents([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredAgents = useMemo(() => {
    return agents.filter((a) => {
      const name = (a.name || a.full_name || '').toLowerCase();
      const email = (a.email || '').toLowerCase();
      const empId = (a.employee_id || '').toLowerCase();
      const query = searchQuery.toLowerCase();

      if (query && !name.includes(query) && !email.includes(query) && !empId.includes(query)) {
        return false;
      }

      if (selectedDept && String(a.department_id) !== String(selectedDept)) {
        return false;
      }

      return true;
    });
  }, [agents, searchQuery, selectedDept]);

  const getDeptName = (deptId) => {
    const dept = departments.find((d) => d.id === deptId);
    return dept ? dept.name : `Department #${deptId}`;
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tight">Support Specialists & Agents</h2>
          <p className="text-xs text-slate-400 mt-1">
            Active roster of department triage specialists, workload capacity, and skill specializations.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Roster</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-3 bg-slate-900/50 p-3 rounded-2xl border border-slate-800/80">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search agents by name, email, or employee ID..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <select
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && <CardSkeleton count={6} />}

      {/* Empty State */}
      {!loading && filteredAgents.length === 0 && (
        <EmptyState
          title="No agents found"
          description={
            searchQuery || selectedDept
              ? 'No agents matched your search query or department filter.'
              : 'No support agents are currently registered in the system.'
          }
          actionLabel={searchQuery || selectedDept ? 'Clear Filters' : 'Refresh'}
          onAction={() => {
            setSearchQuery('');
            setSelectedDept('');
            loadData();
          }}
        />
      )}

      {/* Agents Grid */}
      {!loading && filteredAgents.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map((a) => {
            const name = a.name || a.full_name || 'Agent';
            const initials = name.charAt(0).toUpperCase();
            const currentWorkload = a.current_workload ?? 0;
            const maxWorkload = a.max_workload || a.max_active_tickets || 10;
            const workloadPct = Math.min(100, Math.round((currentWorkload / Math.max(1, maxWorkload)) * 100));
            const isOnline = a.availability !== false && a.is_active !== false;

            return (
              <div key={a.id} className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4 hover:border-slate-700/80 transition-all">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-500 flex items-center justify-center text-slate-950 font-black text-sm shadow-md">
                      {initials}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white">{name}</h4>
                      <p className="text-[11px] text-slate-400 font-mono">{a.employee_id || `AGT-${a.id}`}</p>
                    </div>
                  </div>
                  <span
                    className={`flex items-center gap-1.5 text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      isOnline
                        ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                        : 'text-slate-400 bg-slate-800/50 border-slate-750'
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                    {isOnline ? 'Available' : 'Away'}
                  </span>
                </div>

                {/* Department tag */}
                {a.department_id && (
                  <div className="inline-block">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-brand-500/10 text-brand-300 border border-brand-500/20">
                      {getDeptName(a.department_id)}
                    </span>
                  </div>
                )}

                {/* Workload Progress Bar */}
                <div className="space-y-2 text-xs pt-1 border-t border-slate-800/60">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Active Workload</span>
                    <span className="font-mono font-bold text-white">
                      {currentWorkload} / {maxWorkload} tickets ({workloadPct}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        workloadPct > 80 ? 'bg-rose-500' : workloadPct > 50 ? 'bg-amber-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${workloadPct}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                    <span>Email</span>
                    <span className="font-mono text-slate-300 truncate max-w-[180px]">{a.email}</span>
                  </div>

                  {/* Skills tags */}
                  {Array.isArray(a.skills) && a.skills.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap pt-1.5">
                      {a.skills.map((s, idx) => (
                        <span key={idx} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
