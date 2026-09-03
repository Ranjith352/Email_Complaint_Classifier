import React, { useState } from 'react';
import { X, Sparkles, Send } from 'lucide-react';
import { createComplaint } from '../api/complaints';
import { classifyText } from '../api/ai';

export default function NewComplaintModal({ onClose, onCreated }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [preview, setPreview] = useState(null);
  const [classifying, setClassifying] = useState(false);

  const handlePreview = async () => {
    if (!description.trim() && !title.trim()) return;
    setClassifying(true);
    try {
      const res = await classifyText(`${title} ${description}`);
      setPreview(res);
    } catch (err) {
      console.error(err);
    } finally {
      setClassifying(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim() || !senderEmail.trim()) return;
    setSubmitting(true);
    try {
      const created = await createComplaint({
        title,
        description,
        sender_email: senderEmail,
      });
      if (onCreated) onCreated(created);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl rounded-2xl glass-modal border border-slate-700/80 p-6 flex flex-col shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-brand-400" />
            <h3 className="text-lg font-bold text-white">Simulate / Submit Customer Complaint</h3>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Customer Email</label>
            <input
              type="email"
              required
              value={senderEmail}
              onChange={(e) => setSenderEmail(e.target.value)}
              placeholder="customer.account@corp.com"
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Email Subject / Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Unauthorized credit card charge on March 2nd"
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-300">Complaint Body / Message</label>
              <button
                type="button"
                onClick={handlePreview}
                disabled={classifying}
                className="text-[11px] text-brand-400 hover:underline flex items-center gap-1"
              >
                <Sparkles className="w-3 h-3" />
                <span>{classifying ? 'Analyzing NLP...' : 'Test Real-time NLP Triage'}</span>
              </button>
            </div>
            <textarea
              rows={5}
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the complaint in detail..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          {preview && (
            <div className="p-3 rounded-xl bg-slate-900/90 border border-brand-500/30 text-xs space-y-1.5 animate-fade-in">
              <p className="text-[11px] font-bold uppercase text-brand-400">Predicted Classification Preview:</p>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200">Dept: <b>{preview.department}</b></span>
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200">Category: <b>{preview.category}</b></span>
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200">Urgency: <b>{preview.urgency}</b></span>
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200">Confidence: <b>{Math.round(preview.confidence * 100)}%</b></span>
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20 disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{submitting ? 'Submitting...' : 'Ingest & Classify'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
