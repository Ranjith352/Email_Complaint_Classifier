import React, { useState } from 'react';
import { Sparkles, Send, Bot, User, BookOpen, ShieldCheck } from 'lucide-react';
import apiClient from '../api/client';

export default function AIAssistantPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Hello! I am your AutoTriage Policy & SOP Assistant. Ask me anything regarding our company refund guidelines, SLA timelines, IT incident procedures, or department escalation rules.',
      citations: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const res = await apiClient.post('/ai/chat', { message: userMsg });
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: res.data.reply,
          citations: res.data.cited_documents || [],
          provider: res.data.provider
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: 'Unable to query knowledge base at this moment. Please verify backend connectivity.',
          citations: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in flex flex-col h-[calc(100vh-8rem)]">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">Internal Policy & RAG AI Assistant</h2>
        <p className="text-xs text-slate-400 mt-1">
          Grounded conversational assistant querying company SOPs, refund policies, and escalation guidelines.
        </p>
      </div>

      {/* Chat Messages Area */}
      <div className="flex-1 glass-panel rounded-2xl border border-slate-800/80 p-5 overflow-y-auto space-y-4">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex items-start gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.role === 'assistant' && (
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-500 flex items-center justify-center text-slate-950 shrink-0 shadow">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed ${
              m.role === 'user'
                ? 'bg-brand-600 text-white shadow-md'
                : 'bg-slate-900 border border-slate-800 text-slate-200'
            }`}>
              <p className="whitespace-pre-wrap">{m.text}</p>

              {m.citations?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-1.5">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                    <BookOpen className="w-3 h-3 text-brand-400" /> Grounded Policy Citations (pgvector):
                  </p>
                  {m.citations.map((c, i) => (
                    <div key={i} className="text-[11px] p-2 rounded bg-slate-950 border border-slate-800 text-slate-300">
                      <span className="font-bold text-white block">{c.title}</span>
                      <span className="text-slate-400 text-[10px] line-clamp-2">{c.content_snippet}</span>
                    </div>
                  ))}
                </div>
              )}

              {m.provider && (
                <p className="text-[10px] font-mono text-slate-500 mt-2">
                  Engine: {m.provider}
                </p>
              )}
            </div>

            {m.role === 'user' && (
              <div className="w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center text-slate-300 shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-slate-400 animate-pulse pl-11">
            <Sparkles className="w-3.5 h-3.5 text-brand-400" />
            <span>Consulting pgvector and company knowledge base...</span>
          </div>
        )}
      </div>

      {/* Input bar */}
      <form onSubmit={handleSend} className="flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about refund timeframes, critical SLA rules, courier replacement procedures..."
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="flex items-center gap-1.5 px-6 py-3 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20 disabled:opacity-50"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Ask Copilot</span>
        </button>
      </form>
    </div>
  );
}
