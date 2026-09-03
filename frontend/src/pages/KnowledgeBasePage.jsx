import React, { useState, useEffect } from 'react';
import { BookOpen, Plus, ShieldCheck, Search, FileText } from 'lucide-react';
import apiClient from '../api/client';

export default function KnowledgeBasePage() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Billing / Payment');
  const [docType, setDocType] = useState('POLICY');
  const [content, setContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadDocs();
  }, []);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/knowledge');
      setDocs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setSubmitting(true);
    try {
      await apiClient.post('/knowledge', {
        title,
        category,
        document_type: docType,
        content_text: content
      });
      setTitle('');
      setContent('');
      setShowAdd(false);
      loadDocs();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tight">Corporate Knowledge Base & Policies</h2>
          <p className="text-xs text-slate-400 mt-1">
            Official operational procedures, refund guidelines, and SLA policies indexed for pgvector RAG retrieval.
          </p>
        </div>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow"
        >
          <Plus className="w-4 h-4" />
          <span>Add New Policy Document</span>
        </button>
      </div>

      {showAdd && (
        <form onSubmit={handleCreate} className="glass-panel p-6 rounded-2xl border border-brand-500/30 space-y-4 animate-fade-in">
          <h3 className="text-sm font-bold text-white">Upload / Author Policy Document</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">Document Title</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. VIP Chargeback Handling Guideline"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">Applicable Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
              >
                <option value="Billing / Payment">Billing / Payment</option>
                <option value="Technical Problem">Technical Problem</option>
                <option value="Security Issue">Security Issue</option>
                <option value="Customer Support">Customer Support</option>
                <option value="Operations & Admin">Operations & Admin</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">Document Type</label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
              >
                <option value="POLICY">Corporate Policy</option>
                <option value="REFUND_GUIDELINE">Refund Guideline</option>
                <option value="SLA_DOC">SLA Procedure</option>
                <option value="SOP">Standard Operating Procedure (SOP)</option>
                <option value="ESCALATION">Escalation Guideline</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">Policy Content Text (Embedded via 384d Vectors)</label>
            <textarea
              rows={4}
              required
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="State the official rules, steps, and conditions..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowAdd(false)}
              className="px-4 py-2 rounded-xl text-xs bg-slate-800 text-slate-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white"
            >
              {submitting ? 'Vectorizing & Saving...' : 'Save & Index to pgvector'}
            </button>
          </div>
        </form>
      )}

      {/* Documents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {docs.map((d) => (
          <div key={d.id} className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20">
                {d.document_type}
              </span>
              <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> 384d Vector Indexed
              </span>
            </div>
            <h3 className="text-sm font-bold text-white">{d.title}</h3>
            <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-900">
              {d.chunk_text}
            </p>
            <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
              <span>Category: {d.category}</span>
              <span>Updated: {new Date(d.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
