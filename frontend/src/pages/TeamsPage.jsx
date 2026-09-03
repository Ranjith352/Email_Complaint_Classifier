import React, { useState, useEffect } from 'react';
import { Users, Shield, ArrowRight } from 'lucide-react';
import apiClient from '../api/client';

export default function TeamsPage() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/teams');
      setTeams(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">Functional Teams</h2>
        <p className="text-xs text-slate-400 mt-1">
          Specialized sub-department operational units handling specific category ticket queues.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {teams.map((t) => (
          <div key={t.id} className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white">{t.name}</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">{t.description || 'Specialized triage and resolution team.'}</p>
            <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
              <span>Department ID: #{t.department_id}</span>
              <span className="text-brand-400 font-semibold">Online</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
