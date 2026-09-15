import React, { useState } from 'react';
import { X, Sparkles, Send, Paperclip, CheckCircle2, ShieldCheck, Clock, UserCheck, Layers } from 'lucide-react';
import { createComplaint } from '../api/complaints';
import { classifyText } from '../api/ai';

export default function NewComplaintModal({ onClose, onCreated }) {
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [source, setSource] = useState('WEB');
  const [attachmentName, setAttachmentName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [preview, setPreview] = useState(null);
  const [classifying, setClassifying] = useState(false);
  const [createdResult, setCreatedResult] = useState(null);

  const handlePreview = async () => {
    if (!description.trim() && !subject.trim()) return;
    setClassifying(true);
    try {
      const res = await classifyText(`${subject} ${description}`);
      setPreview(res);
    } catch (err) {
      console.error(err);
    } finally {
      setClassifying(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setAttachmentName(file.name);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim() || !customerEmail.trim()) return;
    setSubmitting(true);
    try {
      const created = await createComplaint({
        customer_name: customerName.trim() || 'Customer',
        customer_email: customerEmail.trim(),
        subject: subject.trim(),
        title: subject.trim(),
        description: description.trim(),
        body: description.trim(),
        source: source,
        attachment_name: attachmentName || null,
      });

      setCreatedResult(created);
      if (onCreated) onCreated(created);
    } catch (err) {
      console.error('Error creating complaint:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl rounded-2xl glass-modal border border-slate-700/80 p-6 flex flex-col shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-brand-400" />
            <h3 className="text-lg font-bold text-white">Intake New Complaint</h3>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {createdResult ? (
          <div className="space-y-4 py-2 animate-fade-in">
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-start gap-3">
              <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-emerald-300">Complaint Successfully Ingested & Triaged</h4>
                <p className="text-xs text-slate-300 mt-1">
                  The automated 9-stage pipeline analyzed the complaint, verified duplicates, determined department & team, assigned an agent, dispatched in-app notifications, and started SLA governance.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-900/90 rounded-xl border border-slate-800 space-y-1">
                <span className="text-slate-400 text-[11px] block">Complaint Ticket ID</span>
                <span className="text-sm font-bold text-brand-400">{createdResult.ticket_number}</span>
              </div>
              <div className="p-3 bg-slate-900/90 rounded-xl border border-slate-800 space-y-1">
                <span className="text-slate-400 text-[11px] block">Source Channel</span>
                <span className="text-sm font-semibold text-slate-200">{createdResult.source || source}</span>
              </div>
              <div className="p-3 bg-slate-900/90 rounded-xl border border-slate-800 space-y-1">
                <span className="text-slate-400 text-[11px] block">Department & Team</span>
                <span className="text-sm font-bold text-slate-100">
                  {createdResult.department?.name || 'Assigned'}
                </span>
                {createdResult.team?.name && (
                  <span className="text-[11px] text-slate-400 block">{createdResult.team.name}</span>
                )}
              </div>
              <div className="p-3 bg-slate-900/90 rounded-xl border border-slate-800 space-y-1">
                <span className="text-slate-400 text-[11px] block">Priority & SLA</span>
                <span className="text-sm font-bold text-rose-400">
                  {createdResult.priority_level || 'HIGH'}
                </span>
                <span className="text-[11px] text-slate-400 block">
                  {createdResult.sla_deadline ? `Deadline: ${new Date(createdResult.sla_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'SLA Started'}
                </span>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Customer Name</label>
                <input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="e.g. Alex Henderson"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Customer Email <span className="text-rose-400">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={customerEmail}
                  onChange={(e) => setCustomerEmail(e.target.value)}
                  placeholder="customer.account@corp.com"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Subject <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g. Duplicate debit charge for transaction TX-9921"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Source Channel</label>
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="WEB">WEB (Portal Intake)</option>
                  <option value="EMAIL">EMAIL (Inbound Message)</option>
                  <option value="MANUAL">MANUAL (Agent / Phone Call)</option>
                </select>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-300">
                  Complaint Description <span className="text-rose-400">*</span>
                </label>
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
                rows={4}
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the complaint in detail (amounts, transaction references, error messages)..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Attachment</label>
              <div className="flex items-center gap-3">
                <label className="cursor-pointer flex items-center gap-2 px-3 py-2 bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl text-xs text-slate-300 transition-colors">
                  <Paperclip className="w-3.5 h-3.5 text-slate-400" />
                  <span>{attachmentName ? 'Change File' : 'Attach File / Screenshot'}</span>
                  <input type="file" onChange={handleFileChange} className="hidden" />
                </label>
                {attachmentName && (
                  <span className="text-xs text-brand-400 font-medium truncate max-w-xs">
                    {attachmentName}
                  </span>
                )}
              </div>
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
                <span>{submitting ? 'Running AI Pipeline...' : 'Submit & Execute Pipeline'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
