import React, { useState } from 'react';
import { Sparkles, Play, ShieldAlert, BookOpen, Layers, CheckCircle } from 'lucide-react';
import { classifyText, summarizeComplaint, getResolutionRecommendations } from '../api/ai';
import UrgencyBadge from '../components/UrgencyBadge';
import DepartmentBadge from '../components/DepartmentBadge';

const PRESET_PROMPTS = [
  {
    title: 'Double Billing & Overcharge',
    text: 'I was charged twice on my credit card for invoice #INV-9284 ($149.00). The transaction appeared twice on my bank statement on March 2nd. I need an immediate refund and cancellation of duplicate transaction!'
  },
  {
    title: '500 Server Outage & Crash',
    text: 'Our team is unable to login to the production portal. The server is throwing 500 internal server error and connection timeouts across all endpoints since 9:00 AM. This is blocking all operations!'
  },
  {
    title: 'Account Security Breach',
    text: 'Someone logged into my account from a strange IP address in another country. My password was changed without my permission and two unauthorized transactions were initiated. Freeze my account immediately!'
  }
];

export default function AIPlaygroundPage() {
  const [inputText, setInputText] = useState(PRESET_PROMPTS[0].text);
  const [running, setRunning] = useState(false);
  const [classification, setClassification] = useState(null);
  const [summary, setSummary] = useState(null);
  const [recommendations, setRecommendations] = useState(null);

  const handleSimulate = async () => {
    if (!inputText.trim()) return;
    setRunning(true);
    try {
      const [classRes, sumRes, recRes] = await Promise.all([
        classifyText(inputText),
        summarizeComplaint(null, inputText),
        getResolutionRecommendations(null, inputText),
      ]);
      setClassification(classRes);
      setSummary(sumRes);
      setRecommendations(recRes);
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">AI & pgvector RAG Simulator</h2>
        <p className="text-xs text-slate-400 mt-1">
          Test any customer message against the complete NLP classification pipeline, Sentence Transformers embeddings, and Groq/Ollama RAG models.
        </p>
      </div>

      {/* Input area */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-300">Test Input Complaint</label>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-500">Quick Samples:</span>
            {PRESET_PROMPTS.map((p) => (
              <button
                key={p.title}
                onClick={() => setInputText(p.text)}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700"
              >
                {p.title}
              </button>
            ))}
          </div>
        </div>

        <textarea
          rows={4}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-xs text-white leading-relaxed focus:outline-none focus:border-brand-500"
          placeholder="Paste or type any customer email..."
        />

        <div className="flex justify-end">
          <button
            onClick={handleSimulate}
            disabled={running}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/25 transition-all hover:scale-[1.02] disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${running ? 'animate-spin' : ''}`} />
            <span>{running ? 'Executing NLP & RAG...' : 'Run Pipeline Simulation'}</span>
          </button>
        </div>
      </div>

      {/* Results grid */}
      {(classification || summary || recommendations) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in">
          
          {/* Column 1: Classification & Entities */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-brand-400 flex items-center gap-1.5">
              <Layers className="w-4 h-4" /> Multi-Label Classification
            </h3>

            {classification && (
              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <span className="text-slate-400">Department</span>
                  <DepartmentBadge department={classification.department} />
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <span className="text-slate-400">Category</span>
                  <span className="font-semibold text-white">{classification.category}</span>
                </div>
                {classification.sub_department && (
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <span className="text-slate-400">Sub-Dept</span>
                    <span className="text-slate-300 font-medium">{classification.sub_department}</span>
                  </div>
                )}
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <span className="text-slate-400">Urgency</span>
                  <UrgencyBadge urgency={classification.urgency} />
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <span className="text-slate-400">Confidence</span>
                  <span className="font-mono font-bold text-emerald-400">{Math.round(classification.confidence * 100)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Sentiment</span>
                  <span className="font-semibold text-purple-400">{classification.sentiment}</span>
                </div>

                {classification.entities && (
                  <div className="pt-2">
                    <p className="text-[10px] text-slate-500 uppercase font-semibold mb-1">Entities Extracted:</p>
                    <pre className="p-2.5 rounded-lg bg-slate-950 text-[10px] font-mono text-slate-300 overflow-x-auto">
                      {JSON.stringify(classification.entities, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Column 2: AI Summarization */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4" /> AI Executive Summary
            </h3>

            {summary && (
              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-200 leading-relaxed font-medium">
                  {summary.summary}
                </div>
                <div>
                  <p className="text-[11px] font-bold text-slate-400 uppercase mb-1">Key Action Items:</p>
                  <ul className="list-disc list-inside space-y-1 text-slate-300">
                    {summary.key_points?.map((pt, i) => (
                      <li key={i}>{pt}</li>
                    ))}
                  </ul>
                </div>
                <p className="text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800">
                  Inference Engine: {summary.provider}
                </p>
              </div>
            )}
          </div>

          {/* Column 3: RAG Grounded Advice */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
              <BookOpen className="w-4 h-4" /> pgvector RAG Resolution
            </h3>

            {recommendations && (
              <div className="space-y-3 text-xs">
                <div className="space-y-2">
                  {recommendations.recommended_steps?.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-2 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 text-slate-300">
                      <span className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <span>{step}</span>
                    </div>
                  ))}
                </div>

                {recommendations.similar_cases?.length > 0 && (
                  <div className="pt-2 border-t border-slate-800">
                    <p className="text-[11px] font-bold text-slate-400 uppercase mb-1.5">Matching Knowledge Cases:</p>
                    {recommendations.similar_cases.map((sc) => (
                      <div key={sc.id} className="p-2 rounded bg-slate-950 border border-slate-800 text-[11px] mb-1.5 flex justify-between items-center text-slate-300">
                        <span className="truncate pr-2 font-medium">{sc.title}</span>
                        <span className="font-mono text-emerald-400 shrink-0">{Math.round(sc.similarity_score * 100)}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}
