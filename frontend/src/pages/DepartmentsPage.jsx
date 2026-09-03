import React, { useState, useEffect } from 'react';
import { Building2, Users, Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import apiClient from '../api/client';

export default function DepartmentsPage() {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDepartments();
  }, []);

  const loadDepartments = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/departments');
      setDepartments(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">Enterprise Departments</h2>
        <p className="text-xs text-slate-400 mt-1">
          Configured organizational departments receiving automated NLP ticket routing.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {departments.map((d) => (
          <div key={d.id} className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs px-2.5 py-0.5 rounded bg-brand-500/10 text-brand-300 font-bold border border-brand-500/20">
                  {d.code}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold">
                  Active Routing
                </span>
              </div>
              <h3 className="text-lg font-bold text-white mt-2">{d.name}</h3>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{d.description}</p>
            </div>

            <div className="pt-4 border-t border-slate-800/80 space-y-2 text-xs text-slate-300">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Department Lead</span>
                <span className="font-medium text-white">{d.lead_name || 'Operations Lead'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Routing Email</span>
                <span className="font-mono text-slate-300">{d.email || `${d.code.toLowerCase()}@company.com`}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Functional Teams</span>
                <span className="font-bold text-brand-400">{d.teams?.length || 4} Teams</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
