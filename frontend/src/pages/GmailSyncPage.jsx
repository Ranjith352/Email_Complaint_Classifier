import React, { useState, useEffect } from 'react';
import { Mail, RefreshCw, CheckCircle2, AlertTriangle, ShieldCheck, ArrowRight, ExternalLink } from 'lucide-react';
import { getGmailStatus, syncGmail } from '../api/gmail';

export default function GmailSyncPage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const res = await getGmailStatus();
      setStatus(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await syncGmail();
      setSyncResult(res);
    } catch (err) {
      setSyncResult({ status: 'error', message: 'Sync request failed.' });
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">Gmail API OAuth 2.0 Ingestion Hub</h2>
        <p className="text-xs text-slate-400 mt-1">
          Automated customer email polling, MIME body decoding, and immediate AI triage pipeline ingestion.
        </p>
      </div>

      {/* Integration Status Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-rose-500/20 to-red-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 shadow-lg">
            <Mail className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Google Gmail Connector</h3>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                status?.configured
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
              }`}>
                {status?.mode || 'Checking...'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Target Inbox Label: <span className="font-mono text-slate-300 font-bold">Complaints</span> · OAuth 2.0 Readonly Scope
            </p>
          </div>
        </div>

        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/25 transition-all hover:scale-[1.02] disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          <span>{syncing ? 'Connecting & Ingesting...' : 'Poll & Sync Emails Now'}</span>
        </button>
      </div>

      {/* Sync Result Banner */}
      {syncResult && (
        <div className={`p-4 rounded-xl border text-xs animate-fade-in flex items-start gap-3 ${
          syncResult.status === 'error'
            ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
            : syncResult.status === 'warning'
            ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
            : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
        }`}>
          {syncResult.status === 'error' ? <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> : <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />}
          <div>
            <p className="font-semibold">{syncResult.message}</p>
            {syncResult.synced_count !== undefined && (
              <p className="text-[11px] opacity-80 mt-0.5">Tickets created: {syncResult.synced_count}</p>
            )}
          </div>
        </div>
      )}

      {/* Architectural Flow Diagram */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-brand-400" /> Automated Pipeline Ingestion Architecture
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="w-6 h-6 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-xs font-bold font-mono">1</span>
            <h4 className="text-xs font-bold text-white">Gmail OAuth Polling</h4>
            <p className="text-[11px] text-slate-400">
              Pulls messages labeled 'Complaints', extracts MIME multi-part body, headers, and sender details.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="w-6 h-6 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-xs font-bold font-mono">2</span>
            <h4 className="text-xs font-bold text-white">NLP & Vector Embedding</h4>
            <p className="text-[11px] text-slate-400">
              Sentence Transformers creates 384d semantic vectors. spaCy extracts entities (order #, txns, amounts).
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="w-6 h-6 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-xs font-bold font-mono">3</span>
            <h4 className="text-xs font-bold text-white">pgvector Semantic RAG</h4>
            <p className="text-[11px] text-slate-400">
              Queries PostgreSQL pgvector for highest cosine similarity matches among historical resolutions and SOPs.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="w-6 h-6 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-xs font-bold font-mono">4</span>
            <h4 className="text-xs font-bold text-white">Generative AI Triage</h4>
            <p className="text-[11px] text-slate-400">
              Groq / Ollama compiles executive summary, step-by-step guidance, and empathetic draft response.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
