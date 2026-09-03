import React, { useState } from 'react';
import { RefreshCw, Sparkles, User, LogOut, CheckCircle2, AlertCircle } from 'lucide-react';
import { syncGmail } from '../api/gmail';

export default function Navbar({ currentUser, onLogout }) {
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState(null);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMessage(null);
    try {
      const res = await syncGmail();
      setSyncMessage({ type: res.status || 'success', text: res.message });
      setTimeout(() => setSyncMessage(null), 5000);
    } catch (err) {
      setSyncMessage({ type: 'error', text: 'Sync error: server unreachable.' });
      setTimeout(() => setSyncMessage(null), 5000);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl px-6 py-3.5">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 text-slate-950 font-black shadow-lg shadow-brand-500/20">
          <Sparkles className="w-5 h-5 text-slate-950" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            AutoTriage <span className="text-xs px-2 py-0.5 rounded-full bg-brand-500/15 text-brand-400 border border-brand-500/30">AI Enterprise</span>
          </h1>
          <p className="text-xs text-slate-400">Intelligent Complaint Classification & RAG Routing</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {syncMessage && (
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs border animate-fade-in ${
            syncMessage.type === 'error' ? 'bg-rose-500/10 text-rose-300 border-rose-500/30' : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
          }`}>
            {syncMessage.type === 'error' ? <AlertCircle className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
            <span>{syncMessage.text}</span>
          </div>
        )}

        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-850 hover:bg-slate-800 text-slate-200 border border-slate-700/80 transition-all hover:border-slate-600 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-brand-400 ${syncing ? 'animate-spin' : ''}`} />
          <span>{syncing ? 'Ingesting...' : 'Sync Gmail'}</span>
        </button>

        <div className="h-6 w-px bg-slate-800" />

        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white text-xs font-bold shadow">
            {currentUser?.full_name ? currentUser.full_name.charAt(0).toUpperCase() : 'A'}
          </div>
          <div className="hidden md:block text-left">
            <p className="text-xs font-semibold text-slate-200">{currentUser?.full_name || 'System Agent'}</p>
            <p className="text-[10px] text-slate-400">{currentUser?.role || 'Operations'} · {currentUser?.department || 'Triage'}</p>
          </div>
          {onLogout && (
            <button
              onClick={onLogout}
              title="Logout"
              className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
