import React, { useState, useEffect } from 'react';
import { ShieldCheck, Clock, FileText, Search, ArrowRight, Database, User, Code } from 'lucide-react';
import apiClient from '../api/client';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedMeta, setSelectedMeta] = useState(null);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/audit');
      setLogs(res.data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter((l) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (l.action && l.action.toLowerCase().includes(q)) ||
      (l.user && l.user.toLowerCase().includes(q)) ||
      (l.entity_type && l.entity_type.toLowerCase().includes(q)) ||
      (l.entity_id && String(l.entity_id).includes(q)) ||
      (l.old_value && l.old_value.toLowerCase().includes(q)) ||
      (l.new_value && l.new_value.toLowerCase().includes(q))
    );
  });

  const getActionColor = (action = '') => {
    const act = action.toLowerCase();
    if (act.includes('create') || act.includes('analysis')) return 'bg-blue-500/15 text-blue-300 border-blue-500/30';
    if (act.includes('resolve') || act.includes('approved')) return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
    if (act.includes('reopen') || act.includes('escalate')) return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    if (act.includes('sent')) return 'bg-purple-500/15 text-purple-300 border-purple-500/30';
    return 'bg-slate-800 text-slate-300 border-slate-700';
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in max-w-7xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-brand-400" />
            <h2 className="text-2xl font-black text-white tracking-tight">Enterprise Audit & Compliance Trail</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Immutable system and user audit records tracking all 13 core operational milestones, state mutations, and responses.
          </p>
        </div>

        <div className="relative w-64">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search action, user, entity..."
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-brand-500"
          />
        </div>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
                <th className="py-3 px-4 font-semibold">Timestamp</th>
                <th className="py-3 px-4 font-semibold">Action</th>
                <th className="py-3 px-4 font-semibold">User / Actor</th>
                <th className="py-3 px-4 font-semibold">Old Value &rarr; New Value</th>
                <th className="py-3 px-4 font-semibold">Entity</th>
                <th className="py-3 px-4 font-semibold text-right">Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredLogs.map((l) => (
                <tr key={l.id} className="hover:bg-slate-900/50 transition-colors">
                  <td className="py-3 px-4 font-mono text-slate-400 text-[11px] whitespace-nowrap">
                    {new Date(l.timestamp || l.created_at).toLocaleString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    })}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold border ${getActionColor(l.action)}`}>
                      {l.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-200 font-medium whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <User className="w-3 h-3 text-slate-500" />
                      <span>{l.user || (l.user_id ? `User #${l.user_id}` : 'System Agent')}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-xs max-w-xs truncate">
                    {l.old_value || l.new_value ? (
                      <div className="flex items-center gap-1.5 font-mono text-[11px]">
                        <span className="text-slate-400 truncate max-w-[120px]" title={l.old_value}>
                          {l.old_value || 'None'}
                        </span>
                        <ArrowRight className="w-3 h-3 text-brand-400 shrink-0" />
                        <span className="text-emerald-300 font-semibold truncate max-w-[150px]" title={l.new_value}>
                          {l.new_value || 'None'}
                        </span>
                      </div>
                    ) : (
                      <span className="text-slate-600 italic">No transition</span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                    {l.entity_type} {l.entity_id ? `#${l.entity_id}` : ''}
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    {l.metadata && Object.keys(l.metadata).length > 0 ? (
                      <button
                        onClick={() => setSelectedMeta({ action: l.action, metadata: l.metadata })}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-300 text-[11px] font-semibold inline-flex items-center gap-1 transition-colors"
                      >
                        <Code className="w-3 h-3" />
                        <span>View JSON</span>
                      </button>
                    ) : (
                      <span className="text-slate-600 text-[11px]">-</span>
                    )}
                  </td>
                </tr>
              ))}
              {filteredLogs.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-slate-500 space-y-2">
                    <Database className="w-8 h-8 text-slate-700 mx-auto" />
                    <p>{loading ? 'Loading enterprise audit entries...' : 'No matching audit records found.'}</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Metadata Detail Modal */}
      {selectedMeta && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <Code className="w-4 h-4 text-brand-400" />
                Audit Metadata: {selectedMeta.action}
              </h4>
              <button
                onClick={() => setSelectedMeta(null)}
                className="text-slate-400 hover:text-white text-xs font-semibold px-2 py-1 rounded bg-slate-800"
              >
                Close
              </button>
            </div>
            <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-emerald-300 font-mono overflow-x-auto max-h-72">
              {JSON.stringify(selectedMeta.metadata, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
