import React, { useState, useEffect } from 'react';
import { Settings, Sliders, Cpu, Mail, Clock, Save, ShieldCheck, AlertCircle } from 'lucide-react';
import apiClient from '../api/client';

export default function SettingsPage() {
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [ollamaModel, setOllamaModel] = useState('llama3.2');
  const [groqModel, setGroqModel] = useState('llama-3.3-70b-versatile');
  
  // Enterprise SLA Configurable Target Rules (Defaults: CRITICAL=2, HIGH=8, MEDIUM=24, LOW=72)
  const [slaRules, setSlaRules] = useState({
    CRITICAL: 2,
    HIGH: 8,
    MEDIUM: 24,
    LOW: 72,
  });
  
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    loadSlaRules();
  }, []);

  const loadSlaRules = async () => {
    try {
      const res = await apiClient.get('/sla-rules');
      if (res.data?.rules) {
        setSlaRules(prev => ({ ...prev, ...res.data.rules }));
      }
    } catch (err) {
      console.warn('Could not fetch SLA rules from backend, using defaults:', err);
    }
  };

  const handleSlaChange = (urgency, value) => {
    setSlaRules(prev => ({
      ...prev,
      [urgency]: Math.max(1, Number(value) || 1),
    }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      // Persist each SLA rule to the backend
      for (const [urgency, hours] of Object.entries(slaRules)) {
        await apiClient.put(`/sla-rules/${urgency}`, { hours });
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 4000);
    } catch (err) {
      console.error('Failed to save SLA rules:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to update SLA configuration.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">System & AI Engine Configuration</h2>
        <p className="text-xs text-slate-400 mt-1">
          Manage local Ollama / Groq providers, SLA target thresholds, and vector embedding parameters.
        </p>
      </div>

      {saved && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold animate-fade-in flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Enterprise SLA configuration and preferences saved successfully.</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-semibold animate-fade-in flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Generative AI Provider */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4 shadow-lg">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-brand-400" /> Generative AI & LLM Provider Abstraction
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Active LLM Provider</label>
              <select
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
              >
                <option value="ollama">Ollama (Default Local Private Execution)</option>
                <option value="groq">Groq Cloud (Optional Ultra-Fast Inference)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Sentence Transformers Model</label>
              <input
                type="text"
                disabled
                value="all-MiniLM-L6-v2 (384 Dimensions)"
                className="w-full bg-slate-950 border border-slate-800/60 rounded-xl px-3 py-2 text-xs text-slate-400 font-mono"
              />
            </div>
          </div>

          {llmProvider === 'ollama' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Ollama Base URL</label>
                <input
                  type="text"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-brand-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Configured Model</label>
                <input
                  type="text"
                  value={ollamaModel}
                  onChange={(e) => setOllamaModel(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-brand-500"
                  placeholder="llama3.2, mistral, or phi3"
                />
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Groq Model</label>
                <input
                  type="text"
                  value={groqModel}
                  onChange={(e) => setGroqModel(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-brand-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Groq API Key Status</label>
                <p className="text-xs text-slate-400 pt-2 font-mono">Configured via .env (GROQ_API_KEY)</p>
              </div>
            </div>
          )}
        </div>

        {/* Configurable SLA Target Rules */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-400" /> Configurable SLA Target Rules (Hours)
            </h3>
            <span className="text-[11px] text-slate-400">Admin Governance</span>
          </div>

          <p className="text-xs text-slate-400">
            Configure target resolution deadlines by priority tier. Warnings are triggered at 75% (Warning), 90% (Critical Warning), and 100% (SLA BREACHED).
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-1">
            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-rose-500/20">
              <label className="block text-xs font-bold text-rose-400 mb-1.5">Critical (P1)</label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min="1"
                  max="168"
                  value={slaRules.CRITICAL}
                  onChange={(e) => handleSlaChange('CRITICAL', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono font-bold focus:outline-none focus:border-rose-400"
                />
                <span className="text-xs text-slate-400">hrs</span>
              </div>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-amber-500/20">
              <label className="block text-xs font-bold text-amber-400 mb-1.5">High (P2)</label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min="1"
                  max="168"
                  value={slaRules.HIGH}
                  onChange={(e) => handleSlaChange('HIGH', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono font-bold focus:outline-none focus:border-amber-400"
                />
                <span className="text-xs text-slate-400">hrs</span>
              </div>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-sky-500/20">
              <label className="block text-xs font-bold text-sky-400 mb-1.5">Medium (P3)</label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min="1"
                  max="168"
                  value={slaRules.MEDIUM}
                  onChange={(e) => handleSlaChange('MEDIUM', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono font-bold focus:outline-none focus:border-sky-400"
                />
                <span className="text-xs text-slate-400">hrs</span>
              </div>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-emerald-500/20">
              <label className="block text-xs font-bold text-emerald-400 mb-1.5">Low (P4)</label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min="1"
                  max="168"
                  value={slaRules.LOW}
                  onChange={(e) => handleSlaChange('LOW', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono font-bold focus:outline-none focus:border-emerald-400"
                />
                <span className="text-xs text-slate-400">hrs</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20 transition-all disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{loading ? 'Saving Changes...' : 'Save Configuration'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
