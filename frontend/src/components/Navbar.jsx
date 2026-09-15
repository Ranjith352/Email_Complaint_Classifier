import React, { useState } from 'react';
import { RefreshCw, Sparkles, User, LogOut, CheckCircle2, AlertCircle, Menu } from 'lucide-react';
import { syncGmail } from '../api/gmail';
import { useToast } from '../context/ToastContext';

export default function Navbar({ currentUser, onLogout, onToggleSidebar }) {
  const [syncing, setSyncing] = useState(false);
  const toast = useToast();

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await syncGmail();
      if (res.status === 'error') {
        toast.error(res.message || 'Gmail sync encountered an error.');
      } else {
        toast.success(res.message || 'Gmail ingested successfully!');
      }
    } catch (err) {
      toast.error('Sync error: server unreachable or Gmail credentials unconfigured.');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl px-4 sm:px-6 py-3.5">
      <div className="flex items-center gap-3">
        {/* Mobile Hamburger Toggle */}
        <button
          type="button"
          onClick={onToggleSidebar}
          className="md:hidden p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800 focus:outline-none"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 text-slate-950 font-black shadow-lg shadow-brand-500/20 shrink-0">
          <Sparkles className="w-5 h-5 text-slate-950" />
        </div>
        <div>
          <h1 className="text-base sm:text-lg font-bold tracking-tight text-white flex items-center gap-2">
            AutoTriage <span className="text-[10px] sm:text-xs px-2 py-0.5 rounded-full bg-brand-500/15 text-brand-400 border border-brand-500/30">AI Enterprise</span>
          </h1>
          <p className="text-[11px] sm:text-xs text-slate-400 hidden sm:block">Intelligent Complaint Classification & RAG Routing</p>
        </div>
      </div>

      <div className="flex items-center gap-3 sm:gap-4">
        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 px-3 sm:px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-700/80 transition-all hover:border-slate-600 disabled:opacity-50 shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-brand-400 ${syncing ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">{syncing ? 'Ingesting...' : 'Sync Gmail'}</span>
          <span className="sm:hidden">{syncing ? '...' : 'Sync'}</span>
        </button>

        <div className="h-6 w-px bg-slate-800" />

        <div className="flex items-center gap-2.5 sm:gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white text-xs font-bold shadow shrink-0">
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
