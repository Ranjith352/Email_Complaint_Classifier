import React, { useState, useEffect } from 'react';
import { ShieldCheck, Clock, FileText } from 'lucide-react';
import apiClient from '../api/client';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/audit');
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">Enterprise Audit & Compliance Logs</h2>
        <p className="text-xs text-slate-400 mt-1">
          Immutable audit trail recording automated routing events, agent assignments, and human-in-the-loop approvals.
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-800/80 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400">
                <th className="py-3 px-4 font-semibold">Timestamp</th>
                <th className="py-3 px-4 font-semibold">Action</th>
                <th className="py-3 px-4 font-semibold">Entity Type</th>
                <th className="py-3 px-4 font-semibold">Entity ID</th>
                <th className="py-3 px-4 font-semibold">Operator / User</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {logs.map((l) => (
                <tr key={l.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                    {new Date(l.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 font-mono font-bold text-brand-300">{l.action}</td>
                  <td className="py-3 px-4 text-slate-300">{l.entity_type}</td>
                  <td className="py-3 px-4 font-mono text-slate-400">#{l.entity_id}</td>
                  <td className="py-3 px-4 text-slate-400">{l.user_id ? `User #${l.user_id}` : 'System Agent'}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-500">
                    {loading ? 'Loading audit records...' : 'No audit entries recorded yet.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
