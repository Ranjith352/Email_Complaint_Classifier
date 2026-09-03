import React, { useState, useEffect } from 'react';
import {
  X, Sparkles, CheckCircle2, Copy, Send, RefreshCw, AlertTriangle,
  ArrowRight, ShieldAlert, FileText, Check, MessageSquare
} from 'lucide-react';
import UrgencyBadge from './UrgencyBadge';
import DepartmentBadge from './DepartmentBadge';
import { resolveComplaint, reassignComplaint } from '../api/complaints';
import { summarizeComplaint, getResolutionRecommendations, generateDraftResponse } from '../api/ai';

export default function ComplaintDetailModal({ complaint, onClose, onUpdated }) {
  const [activeTab, setActiveTab] = useState('insights'); // insights, draft, resolve, details
  const [summary, setSummary] = useState(complaint.ai_summary || null);
  const [summaryPoints, setSummaryPoints] = useState([]);
  const [loadingSummary, setLoadingSummary] = useState(false);
  
  const [recommendations, setRecommendations] = useState([]);
  const [similarCases, setSimilarCases] = useState([]);
  const [loadingRecommend, setLoadingRecommend] = useState(false);

  const [draftSubject, setDraftSubject] = useState('');
  const [draftBody, setDraftBody] = useState(complaint.ai_draft_response || '');
  const [draftTone, setDraftTone] = useState('Empathetic & Professional');
  const [loadingDraft, setLoadingDraft] = useState(false);
  const [copied, setCopied] = useState(false);

  const [resolutionNotes, setResolutionNotes] = useState(complaint.resolution_notes || '');
  const [markAsKnowledge, setMarkAsKnowledge] = useState(true);
  const [resolving, setResolving] = useState(false);

  const [selectedDept, setSelectedDept] = useState(complaint.department);
  const [reassignReason, setReassignReason] = useState('');
  const [reassigning, setReassigning] = useState(false);

  // Auto-fetch AI enrichments if not already present
  useEffect(() => {
    if (!summary) {
      handleFetchSummary();
    }
    handleFetchRecommendations();
  }, [complaint.id]);

  const handleFetchSummary = async () => {
    setLoadingSummary(true);
    try {
      const res = await summarizeComplaint(complaint.id);
      setSummary(res.summary);
      setSummaryPoints(res.key_points || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleFetchRecommendations = async () => {
    setLoadingRecommend(true);
    try {
      const res = await getResolutionRecommendations(complaint.id);
      setRecommendations(res.recommended_steps || []);
      setSimilarCases(res.similar_cases || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingRecommend(false);
    }
  };

  const handleGenerateDraft = async (tone = draftTone) => {
    setLoadingDraft(true);
    try {
      const res = await generateDraftResponse(complaint.id, null, tone);
      setDraftSubject(res.subject);
      setDraftBody(res.body);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDraft(false);
    }
  };

  const handleResolve = async () => {
    if (!resolutionNotes.trim()) return;
    setResolving(true);
    try {
      const updated = await resolveComplaint(complaint.id, resolutionNotes, markAsKnowledge);
      if (onUpdated) onUpdated(updated);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setResolving(false);
    }
  };

  const handleReassign = async () => {
    if (!selectedDept || selectedDept === complaint.department) return;
    setReassigning(true);
    try {
      const updated = await reassignComplaint(complaint.id, selectedDept, null, reassignReason);
      if (onUpdated) onUpdated(updated);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setReassigning(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(draftBody);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl glass-modal border border-slate-700/80 flex flex-col shadow-2xl">
        
        {/* Modal Header */}
        <div className="flex items-start justify-between p-6 border-b border-slate-800/80 bg-slate-900/60">
          <div className="space-y-1.5 pr-6">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-bold border border-slate-700">
                {complaint.ticket_number}
              </span>
              <UrgencyBadge urgency={complaint.urgency} />
              <DepartmentBadge department={complaint.department} />
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                complaint.status === 'Resolved'
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-blue-500/10 text-blue-300 border-blue-500/30'
              }`}>
                {complaint.status}
              </span>
            </div>
            <h2 className="text-xl font-bold text-white mt-1 leading-snug">{complaint.title}</h2>
            <p className="text-xs text-slate-400">
              From: <span className="text-slate-300 font-medium">{complaint.sender_email}</span> · Category: <span className="text-slate-300 font-medium">{complaint.category}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Navigation Tabs */}
        <div className="flex border-b border-slate-800 bg-slate-900/40 px-6 gap-2">
          {[
            { id: 'insights', label: 'AI Triage & RAG Advice', icon: Sparkles },
            { id: 'draft', label: 'Smart Response Drafter', icon: MessageSquare },
            { id: 'details', label: 'Original Message & Entities', icon: FileText },
            { id: 'resolve', label: 'Take Action / Resolve', icon: CheckCircle2 },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-3 px-3 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-brand-500 text-brand-300'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Modal Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          
          {/* TAB 1: AI Triage & RAG Advice */}
          {activeTab === 'insights' && (
            <div className="space-y-6">
              {/* Executive Summary Box */}
              <div className="p-4 rounded-xl bg-gradient-to-br from-slate-900/90 to-slate-900/50 border border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-400">
                    <Sparkles className="w-4 h-4" /> AI Executive Summary
                  </span>
                  <button
                    onClick={handleFetchSummary}
                    disabled={loadingSummary}
                    className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1"
                  >
                    <RefreshCw className={`w-3 h-3 ${loadingSummary ? 'animate-spin' : ''}`} /> Refresh
                  </button>
                </div>
                {loadingSummary ? (
                  <div className="py-4 text-xs text-slate-400 animate-pulse">Analyzing complaint context and extracting key points...</div>
                ) : (
                  <div className="space-y-2 text-xs text-slate-300 leading-relaxed">
                    <p className="font-medium text-slate-200">{summary || 'No summary generated yet.'}</p>
                    {summaryPoints.length > 0 && (
                      <ul className="list-disc list-inside space-y-1 text-slate-400 pt-1">
                        {summaryPoints.map((pt, i) => (
                          <li key={i}>{pt}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>

              {/* RAG-Grounded Step-by-Step Resolution */}
              <div className="p-4 rounded-xl bg-gradient-to-br from-blue-950/20 to-slate-900/80 border border-blue-900/30">
                <div className="flex items-center justify-between mb-3">
                  <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-400">
                    <CheckCircle2 className="w-4 h-4" /> RAG-Grounded Recommended Resolution
                  </span>
                </div>
                {loadingRecommend ? (
                  <div className="py-4 text-xs text-slate-400 animate-pulse">Querying pgvector for similar past resolutions...</div>
                ) : (
                  <div className="space-y-3">
                    <div className="space-y-2">
                      {recommendations.map((step, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                          <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-300 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                            {idx + 1}
                          </span>
                          <span>{step}</span>
                        </div>
                      ))}
                    </div>

                    {similarCases.length > 0 && (
                      <div className="pt-3 border-t border-slate-800/80">
                        <p className="text-[11px] font-semibold text-slate-400 mb-2">Knowledge Base Citations (pgvector similarity):</p>
                        <div className="space-y-1.5">
                          {similarCases.map((sc) => (
                            <div key={sc.id} className="text-[11px] p-2 rounded bg-slate-950/50 border border-slate-800 flex items-center justify-between text-slate-300">
                              <span className="truncate pr-2 font-medium">{sc.title}</span>
                              <span className="text-[10px] font-mono text-emerald-400 shrink-0">
                                {Math.round(sc.similarity_score * 100)}% match
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: Smart Response Drafter */}
          {activeTab === 'draft' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Tone:</span>
                  {['Empathetic & Professional', 'Direct & Technical', 'Urgent Action'].map((tone) => (
                    <button
                      key={tone}
                      onClick={() => {
                        setDraftTone(tone);
                        handleGenerateDraft(tone);
                      }}
                      className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                        draftTone === tone
                          ? 'bg-brand-500/20 text-brand-300 border-brand-500/40'
                          : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                      }`}
                    >
                      {tone}
                    </button>
                  ))}
                </div>

                <button
                  onClick={() => handleGenerateDraft(draftTone)}
                  disabled={loadingDraft}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white shadow-sm disabled:opacity-50"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${loadingDraft ? 'animate-spin' : ''}`} />
                  <span>{loadingDraft ? 'Generating Draft...' : 'Generate New Draft'}</span>
                </button>
              </div>

              {draftSubject && (
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Email Subject</label>
                  <input
                    type="text"
                    value={draftSubject}
                    onChange={(e) => setDraftSubject(e.target.value)}
                    className="w-full bg-slate-900/80 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                  />
                </div>
              )}

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase">Response Body</label>
                  {draftBody && (
                    <button
                      onClick={handleCopy}
                      className="flex items-center gap-1 text-xs text-slate-400 hover:text-brand-300"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-brand-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? 'Copied to clipboard!' : 'Copy to clipboard'}</span>
                    </button>
                  )}
                </div>
                <textarea
                  rows={9}
                  value={draftBody}
                  onChange={(e) => setDraftBody(e.target.value)}
                  placeholder="Click 'Generate New Draft' to let Generative AI compose a tailored email response..."
                  className="w-full bg-slate-900/80 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 font-sans leading-relaxed focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>
          )}

          {/* TAB 3: Original Message & Entities */}
          {activeTab === 'details' && (
            <div className="space-y-5">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Original Email Content</h4>
                <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {complaint.description}
                </div>
              </div>

              {complaint.entities && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Extracted Entities (spaCy & Regex)</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <p className="text-[10px] text-slate-400 uppercase">Transaction IDs</p>
                      <p className="text-xs font-mono font-semibold text-emerald-400 mt-1">
                        {complaint.entities.transaction_ids?.length ? complaint.entities.transaction_ids.join(', ') : 'None'}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <p className="text-[10px] text-slate-400 uppercase">Order IDs</p>
                      <p className="text-xs font-mono font-semibold text-blue-400 mt-1">
                        {complaint.entities.order_ids?.length ? complaint.entities.order_ids.join(', ') : 'None'}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <p className="text-[10px] text-slate-400 uppercase">Detected Amounts</p>
                      <p className="text-xs font-mono font-semibold text-amber-400 mt-1">
                        {complaint.entities.amounts?.length ? complaint.entities.amounts.join(', ') : 'None'}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <p className="text-[10px] text-slate-400 uppercase">Sentiment</p>
                      <p className="text-xs font-semibold text-purple-400 mt-1">{complaint.sentiment || 'Neutral'}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: Take Action / Resolve */}
          {activeTab === 'resolve' && (
            <div className="space-y-6">
              {/* Resolve Ticket Section */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> Mark Complaint as Resolved
                </h4>
                <p className="text-xs text-slate-400">
                  Document the final corrective action taken. This will fulfill SLA timers and optionally index the solution into the pgvector RAG database.
                </p>
                <textarea
                  rows={3}
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="e.g., Refund issued via Stripe transaction #REF-9921. Customer confirmed receipt via email."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                />
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={markAsKnowledge}
                      onChange={(e) => setMarkAsKnowledge(e.target.checked)}
                      className="rounded bg-slate-800 border-slate-700 text-brand-600 focus:ring-0"
                    />
                    <span>Index solution into RAG Knowledge Base for future automated triage</span>
                  </label>
                  <button
                    onClick={handleResolve}
                    disabled={resolving || !resolutionNotes.trim()}
                    className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all disabled:opacity-50 shadow-md shadow-emerald-600/20"
                  >
                    {resolving ? 'Saving...' : 'Resolve Ticket'}
                  </button>
                </div>
              </div>

              {/* Reassign Department Section */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                  <ArrowRight className="w-4 h-4" /> Reassign Department
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] text-slate-400 uppercase mb-1">Target Department</label>
                    <select
                      value={selectedDept}
                      onChange={(e) => setSelectedDept(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                    >
                      <option value="IT">IT & Infrastructure</option>
                      <option value="Finance">Finance & Billing</option>
                      <option value="Security">Security & Compliance</option>
                      <option value="Support">Customer Support</option>
                      <option value="Operations">Operations & Administration</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-400 uppercase mb-1">Reason for Reassignment</label>
                    <input
                      type="text"
                      value={reassignReason}
                      onChange={(e) => setReassignReason(e.target.value)}
                      placeholder="e.g., Escalation requires security operations review."
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                    />
                  </div>
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={handleReassign}
                    disabled={reassigning || selectedDept === complaint.department}
                    className="px-4 py-2 rounded-xl text-xs font-bold bg-amber-600 hover:bg-amber-500 text-white transition-all disabled:opacity-50"
                  >
                    {reassigning ? 'Reassigning...' : 'Reassign Ticket'}
                  </button>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
