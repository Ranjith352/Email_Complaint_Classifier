import React, { useState } from 'react';
import { Settings, Sliders, Cpu, Mail, Clock, Save, ShieldCheck } from 'lucide-react';

export default function SettingsPage() {
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [ollamaModel, setOllamaModel] = useState('llama3.2');
  const [groqModel, setGroqModel] = useState('llama-3.3-70b-versatile');
  const [slaCritical, setSlaCritical] = useState(4);
  const [slaHigh, setSlaHigh] = useState(8);
  const [slaMedium, setSlaMedium] = useState(24);
  const [slaLow, setSlaLow] = useState(48);
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in max-w-4xl">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">System & AI Engine Configuration</h2>
        <p className="text-xs text-slate-400 mt-1">
          Manage local Ollama / Groq providers, SLA target thresholds, and vector embedding parameters.
        </p>
      </div>

      {saved && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold animate-fade-in flex items-center gap-2">
          <ShieldCheck className="w-4 h-4" />
          <span>Configuration preferences saved successfully.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        
        {/* Generative AI Provider */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-brand-400" /> Generative AI & LLM Provider Abstraction
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Active LLM Provider</label>
              <select
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
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
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Configured Model</label>
                <input
                  type="text"
                  value={ollamaModel}
                  onChange={(e) => setOllamaModel(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono"
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
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Groq API Key Status</label>
                <p className="text-xs text-slate-400 pt-2 font-mono">Managed via .env (GROQ_API_KEY)</p>
              </div>
            </div>
          )}
        </div>

        {/* SLA Target Rules */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-400" /> SLA Target Resolution Hours
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-rose-400 mb-1">Critical (P1)</label>
              <input
                type="number"
                value={slaCritical}
                onChange={(e) => setSlaCritical(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-amber-400 mb-1">High (P2)</label>
              <input
                type="number"
                value={slaHigh}
                onChange={(e) => setSlaHigh(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-sky-400 mb-1">Medium (P3)</label>
              <input
                type="number"
                value={slaMedium}
                onChange={(e) => setSlaMedium(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-emerald-400 mb-1">Low (P4)</label>
              <input
                type="number"
                value={slaLow}
                onChange={(e) => setSlaLow(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20"
          >
            <Save className="w-4 h-4" />
            <span>Save Configuration</span>
          </button>
        </div>
      </form>
    </div>
  );
}
