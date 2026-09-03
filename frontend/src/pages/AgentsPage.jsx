import React, { useState, useEffect } from 'react';
import { UserCheck, Shield, Activity, Mail } from 'lucide-react';
import apiClient from '../api/client';

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/agents');
      setAgents(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">Support Specialists & Agents</h2>
        <p className="text-xs text-slate-400 mt-1">
          Active roster of department triage specialists, workload capacity, and skill specializations.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((a) => (
          <div key={a.id} className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-500 flex items-center justify-center text-slate-950 font-bold text-sm">
                  {a.full_name.charAt(0)}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">{a.full_name}</h4>
                  <p className="text-[11px] text-slate-400">{a.employee_id}</p>
                </div>
              </div>
              <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Online
              </span>
            </div>

            <div className="space-y-2 text-xs pt-1 border-t border-slate-800/60">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Active Workload</span>
                <span className="font-mono font-bold text-white">{a.current_workload} / {a.max_active_tickets} tickets</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-brand-500 h-full rounded-full"
                  style={{ width: `${Math.min(100, (a.current_workload / a.max_active_tickets) * 100)}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                <span>Email</span>
                <span className="font-mono text-slate-300">{a.email}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
