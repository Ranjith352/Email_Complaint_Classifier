import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Sparkles, CheckCircle2, ShieldAlert, Clock, User,
  FileText, MessageSquare, AlertCircle, RefreshCw, Copy, Check, ThumbsUp, ThumbsDown
} from 'lucide-react';
import UrgencyBadge from '../components/UrgencyBadge';
import DepartmentBadge from '../components/DepartmentBadge';
import { getComplaint, resolveComplaint, reassignComplaint } from '../api/complaints';
import apiClient from '../api/client';

export default function ComplaintDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolving, setResolving] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [feedbackNotes, setFeedbackNotes] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [copiedDraft, setCopiedDraft] = useState(false);

  useEffect(() => {
    loadDetails();
  }, [id]);

  const loadDetails = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(`/complaints/${id}`);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!resolutionNotes.trim()) return;
    setResolving(true);
    try {
      await resolveComplaint(id, resolutionNotes, true);
      loadDetails();
    } catch (err) {
      console.error(err);
    } finally {
      setResolving(false);
    }
  };

  const handleApproveResponse = async (respId) => {
    try {
      await apiClient.post(`/complaints/${id}/approve-response?response_id=${respId}`);
      loadDetails();
    } catch (err) {
      console.error(err);
    }
  };

  const handleFeedback = async (isCorrect) => {
    try {
      await apiClient.post(`/complaints/${id}/feedback`, {
        is_category_correct: isCorrect,
        is_sentiment_correct: isCorrect,
        rating: feedbackRating,
        notes: feedbackNotes || (isCorrect ? 'AI routing verified correct.' : 'Incorrect routing.')
      });
      setFeedbackSubmitted(true);
      loadDetails();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="p-8 text-xs text-slate-400 font-mono">Loading complaint ticket #{id}...</div>;
  }

  if (!data?.complaint) {
    return (
      <div className="p-8 space-y-4">
        <p className="text-sm text-rose-400">Complaint ticket not found.</p>
        <button onClick={() => navigate('/complaints')} className="text-xs text-brand-400 flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Complaints
        </button>
      </div>
    );
  }

  const c = data.complaint;
  const draftResponse = data.ai_responses?.find(r => r.response_type === 'DRAFT_REPLY');
  const summaryResponse = data.ai_responses?.find(r => r.response_type === 'SUMMARY');

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Back button & Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <button
          onClick={() => navigate('/complaints')}
          className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Complaints Explorer</span>
        </button>

        <div className="flex items-center gap-3">
          <span className="text-xs px-2.5 py-1 rounded-full font-semibold border bg-blue-500/10 text-blue-300 border-blue-500/30">
            Priority: {c.priority_level} ({Math.round(c.priority_score)}/100)
          </span>
          <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
            c.status === 'Resolved' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' : 'bg-slate-800 text-slate-300 border-slate-700'
          }`}>
            {c.status}
          </span>
        </div>
      </div>

      {/* Ticket Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-3">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="font-mono text-sm px-3 py-1 rounded bg-slate-900 border border-slate-700 text-brand-400 font-bold">
            {c.ticket_number}
          </span>
          <UrgencyBadge urgency={c.urgency} />
          <DepartmentBadge department={c.category} />
          {c.is_duplicate && (
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
              Duplicate Ticket
            </span>
          )}
        </div>
        <h2 className="text-2xl font-black text-white">{c.subject}</h2>
        <div className="flex items-center gap-4 text-xs text-slate-400 flex-wrap">
          <span>Customer: <b className="text-slate-200">{c.customer_name || 'Customer'}</b> ({c.customer_email})</span>
          <span>Source: <b className="text-slate-200">{c.source}</b></span>
          <span>SLA Target: <b className="text-slate-200">{c.sla_deadline ? new Date(c.sla_deadline).toLocaleString() : 'N/A'}</b></span>
        </div>
      </div>

      {/* Grid: Complaint Body + AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Body, Entities & Timeline */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Customer Communication Message</h3>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
              {c.body}
            </div>
          </div>

          {/* Extracted Entities */}
          {data.entities?.length > 0 && (
            <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Recognized Named Entities (NER)</h3>
              <div className="flex items-center gap-2 flex-wrap">
                {data.entities.map((e, idx) => (
                  <div key={idx} className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
                    <span className="text-[10px] text-slate-500 uppercase block">{e.entity_type}</span>
                    <span className="font-mono font-bold text-emerald-400">{e.entity_value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Customer Response (Requires Human Approval) */}
          {draftResponse && (
            <div className="glass-panel p-6 rounded-2xl border border-blue-900/40 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-blue-400" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-blue-300">
                    AI-Generated Customer Response (Ollama / Groq)
                  </h3>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                  draftResponse.is_approved
                    ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                    : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                }`}>
                  {draftResponse.is_approved ? `Approved by ${draftResponse.approved_by || 'Agent'}` : 'Pending Human Approval'}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
                {draftResponse.content}
              </div>

              <div className="flex items-center justify-between pt-2">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(draftResponse.content);
                    setCopiedDraft(true);
                    setTimeout(() => setCopiedDraft(false), 2000);
                  }}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5"
                >
                  {copiedDraft ? <Check className="w-3.5 h-3.5 text-brand-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedDraft ? 'Copied to Clipboard' : 'Copy Text'}</span>
                </button>

                {!draftResponse.is_approved && (
                  <button
                    onClick={() => handleApproveResponse(draftResponse.id)}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Approve & Authorize Response</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Audit & Event Log */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Ticket Event Timeline</h3>
            <div className="space-y-2">
              {data.events?.map((ev) => (
                <div key={ev.id} className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex items-start justify-between text-xs">
                  <div>
                    <span className="font-bold text-white font-mono text-[11px] uppercase mr-2">[{ev.event_type}]</span>
                    <span className="text-slate-300">{ev.notes || 'System action recorded.'}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 shrink-0 ml-2">
                    {new Date(ev.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: AI Summary, Human Feedback & Resolution */}
        <div className="space-y-6">
          
          {/* Executive Summary */}
          {summaryResponse && (
            <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-brand-400 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4" /> AI Executive Summary
              </h3>
              <p className="text-xs text-slate-200 leading-relaxed">
                {summaryResponse.content}
              </p>
            </div>
          )}

          {/* Human-In-The-Loop AI Feedback Collection */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-purple-400">Model Accuracy Feedback</h3>
            <p className="text-[11px] text-slate-400">
              Was the AI category & routing correct? Feedback informs future model fine-tuning.
            </p>
            {feedbackSubmitted ? (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300">
                Thank you! Your feedback was saved to the training dataset.
              </div>
            ) : (
              <div className="space-y-2 pt-1">
                <div className="flex gap-2">
                  <button
                    onClick={() => handleFeedback(true)}
                    className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold bg-slate-900 hover:bg-emerald-600/20 text-emerald-300 border border-slate-800 hover:border-emerald-500/40"
                  >
                    <ThumbsUp className="w-3.5 h-3.5" /> Correct
                  </button>
                  <button
                    onClick={() => handleFeedback(false)}
                    className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold bg-slate-900 hover:bg-rose-600/20 text-rose-300 border border-slate-800 hover:border-rose-500/40"
                  >
                    <ThumbsDown className="w-3.5 h-3.5" /> Inaccurate
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Resolve Ticket Action */}
          {c.status !== 'Resolved' && (
            <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> Close / Resolve Complaint
              </h3>
              <textarea
                rows={3}
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="Enter final resolution details..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-brand-500"
              />
              <button
                onClick={handleResolve}
                disabled={resolving || !resolutionNotes.trim()}
                className="w-full py-2.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50"
              >
                {resolving ? 'Resolving...' : 'Confirm Ticket Resolution'}
              </button>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
