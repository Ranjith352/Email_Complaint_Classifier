import React, { useState, useEffect } from 'react';
import {
  X, Sparkles, CheckCircle2, Copy, Send, RefreshCw, AlertTriangle,
  ArrowRight, ShieldAlert, FileText, Check, MessageSquare, Edit3, Save
} from 'lucide-react';
import UrgencyBadge from './UrgencyBadge';
import DepartmentBadge from './DepartmentBadge';
import SLATrackerCard from './SLATrackerCard';
import {
  resolveComplaint, reassignComplaint,
  generateCustomerResponse, editCustomerResponse,
  approveCustomerResponse, sendCustomerResponse
} from '../api/complaints';
import { summarizeComplaint, getResolutionRecommendations } from '../api/ai';
import apiClient from '../api/client';
import { useConfirm } from '../context/ConfirmContext';
import { useToast } from '../context/ToastContext';

export default function ComplaintDetailModal({ complaint, onClose, onUpdated }) {
  const confirm = useConfirm();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState('insights'); // insights, draft, resolve, details
  const [slaMetrics, setSlaMetrics] = useState(complaint.sla_metrics || null);
  const [escalating, setEscalating] = useState(false);
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

  // Response Studio States: Generate, Edit, Approve, Send
  const [draftResponse, setDraftResponse] = useState(null);
  const [isEditingDraft, setIsEditingDraft] = useState(false);
  const [editedDraftText, setEditedDraftText] = useState('');
  const [savingDraftEdit, setSavingDraftEdit] = useState(false);
  const [approvingDraft, setApprovingDraft] = useState(false);
  const [sendingDraft, setSendingDraft] = useState(false);
  const [draftActionFeedback, setDraftActionFeedback] = useState('');

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
    fetchComplaintDetails();
  }, [complaint.id]);

  const fetchComplaintDetails = async () => {
    try {
      const res = await apiClient.get(`/complaints/${complaint.id}`);
      if (res.data?.sla_metrics) {
        setSlaMetrics(res.data.sla_metrics);
      }
      const draft = res.data?.ai_responses?.find(r => r.response_type === 'DRAFT_REPLY');
      if (draft) {
        setDraftResponse(draft);
        setDraftBody(draft.content || '');
        setEditedDraftText(draft.content || '');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleEscalateModal = async (reason) => {
    setEscalating(true);
    try {
      await apiClient.post(`/complaints/${complaint.id}/escalate`, { reason });
      await fetchComplaintDetails();
      if (onUpdated) onUpdated();
    } catch (err) {
      console.error('Failed to escalate complaint:', err);
      alert('Failed to escalate: ' + (err.response?.data?.detail || err.message));
    } finally {
      setEscalating(false);
    }
  };

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

  const handleGenerateAIResponse = async (tone = draftTone) => {
    setLoadingDraft(true);
    setDraftActionFeedback('');
    try {
      const res = await generateCustomerResponse(complaint.id, tone);
      setDraftResponse(res.response);
      setDraftBody(res.response.content);
      setEditedDraftText(res.response.content);
      setIsEditingDraft(false);
      setDraftActionFeedback('Professional AI customer response generated.');
      setTimeout(() => setDraftActionFeedback(''), 4000);
      if (onUpdated) onUpdated({ ...complaint });
    } catch (err) {
      console.error(err);
      alert('Failed to generate customer response: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingDraft(false);
    }
  };

  const handleSaveDraftEdit = async () => {
    if (!editedDraftText.trim() || !draftResponse?.id) return;
    setSavingDraftEdit(true);
    try {
      const res = await editCustomerResponse(complaint.id, draftResponse.id, editedDraftText);
      setDraftResponse(res.response);
      setDraftBody(res.response.content);
      setIsEditingDraft(false);
      setDraftActionFeedback('Draft response updated. Explicit human re-approval required before sending.');
      setTimeout(() => setDraftActionFeedback(''), 4000);
      if (onUpdated) onUpdated({ ...complaint });
    } catch (err) {
      console.error(err);
      alert('Failed to update response draft: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingDraftEdit(false);
    }
  };

  const handleApproveDraft = async () => {
    if (!draftResponse?.id) return;
    setApprovingDraft(true);
    try {
      const res = await approveCustomerResponse(complaint.id, draftResponse.id, 'Support Agent');
      setDraftResponse(res.response);
      setDraftActionFeedback('Response explicitly approved! You may now dispatch it to the customer.');
      setTimeout(() => setDraftActionFeedback(''), 4000);
      if (onUpdated) onUpdated({ ...complaint });
    } catch (err) {
      console.error(err);
      alert('Failed to approve response: ' + (err.response?.data?.detail || err.message));
    } finally {
      setApprovingDraft(false);
    }
  };

  const handleSendDraft = async () => {
    if (!draftResponse?.is_approved) {
      toast.warning('Cannot send response without explicit human approval. Please approve the response before sending.');
      return;
    }
    const recipient = complaint.customer_email || complaint.sender_email || 'the customer';
    const confirmed = await confirm({
      title: 'Dispatch Email Response',
      message: `Are you sure you want to send this approved response to ${recipient}? This will record the milestone and update ticket history.`,
      confirmText: 'Dispatch Email',
      variant: 'info',
    });
    if (!confirmed) {
      return;
    }
    setSendingDraft(true);
    try {
      const res = await sendCustomerResponse(complaint.id, draftResponse.id, 'Support Agent');
      setDraftResponse(res.response);
      toast.success(`Response successfully dispatched to ${recipient}!`);
      setDraftActionFeedback(`Response successfully dispatched to ${recipient}!`);
      setTimeout(() => setDraftActionFeedback(''), 5000);
      if (onUpdated) onUpdated({ ...complaint, status: 'Response Sent' });
    } catch (err) {
      console.error(err);
      toast.error('Failed to send response: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSendingDraft(false);
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
            { id: 'draft', label: 'Customer Response Studio', icon: MessageSquare },
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
              {/* SLA Tracking & Escalation Card */}
              <SLATrackerCard
                slaMetrics={slaMetrics}
                isEscalated={complaint.is_escalated}
                onEscalate={handleEscalateModal}
                loadingEscalate={escalating}
              />

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

              {/* AI Recommended Resolution */}
              <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-950/20 via-slate-900/80 to-slate-950 border border-indigo-500/30 space-y-4 shadow-lg">
                <div className="flex items-start justify-between flex-wrap gap-2 pb-2 border-b border-indigo-500/20">
                  <div className="space-y-1">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                      <Sparkles className="w-3 h-3 text-indigo-400" /> AI GENERATED RECOMMENDATION
                    </span>
                    <h4 className="text-sm font-bold text-white flex items-center gap-1.5 pt-0.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" /> AI Recommended Resolution
                    </h4>
                  </div>
                  <button
                    onClick={handleFetchRecommendations}
                    disabled={loadingRecommend}
                    className="text-[11px] text-slate-400 hover:text-white flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-700 transition-colors"
                  >
                    <RefreshCw className={`w-3 h-3 ${loadingRecommend ? 'animate-spin' : ''}`} /> Refresh
                  </button>
                </div>

                {loadingRecommend ? (
                  <div className="py-4 text-xs text-slate-400 animate-pulse font-mono">Generating grounded resolution steps...</div>
                ) : (
                  <div className="space-y-3">
                    <div className="space-y-2">
                      {recommendations.length > 0 ? (
                        recommendations.map((step, idx) => (
                          <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-200 bg-slate-950/70 p-2.5 rounded-xl border border-slate-800/90 leading-relaxed">
                            <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center justify-center text-[10px] font-mono font-bold shrink-0 mt-0.5">
                              {idx + 1}
                            </span>
                            <span className="font-medium">{step}</span>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-slate-400 italic p-2">No resolution recommendations generated yet.</p>
                      )}
                    </div>

                    {/* Prominent Responsibility Notice */}
                    <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>The agent remains responsible for the final decision.</span>
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

          {/* TAB 2: Customer Response Studio: Generate, Edit, Approve, Send */}
          {activeTab === 'draft' && (
            <div className="space-y-4">
              <div className="flex items-start justify-between flex-wrap gap-3 pb-2 border-b border-slate-800">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-blue-400" />
                    <h3 className="text-sm font-black text-white tracking-wide">
                      Professional Customer Response Studio
                    </h3>
                  </div>
                  <p className="text-xs text-slate-400">
                    AI-crafted professional response. The agent can Generate, Edit, Approve, and Send.
                  </p>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  {draftResponse?.is_sent ? (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40 flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-blue-400" />
                      <span>Sent to Customer</span>
                    </span>
                  ) : draftResponse?.is_approved ? (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Approved by {draftResponse.approved_by || 'Agent'}</span>
                    </span>
                  ) : draftResponse ? (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                      <span>Pending Human Approval</span>
                    </span>
                  ) : (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">
                      No Draft Generated
                    </span>
                  )}
                </div>
              </div>

              {/* Strict Guardrail Policy Notice */}
              <div className="p-3 rounded-xl bg-slate-950/80 border border-amber-500/30 text-amber-200/90 text-xs flex items-center gap-2.5">
                <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
                <span>
                  <b>Strict Policy:</b> Customer responses are <u>never sent automatically</u>. Explicit human approval is required before dispatch.
                </span>
              </div>

              {/* Action Feedback Banner */}
              {draftActionFeedback && (
                <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 text-xs font-medium flex items-center gap-2 animate-fade-in">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>{draftActionFeedback}</span>
                </div>
              )}

              {/* Tone Selection */}
              <div className="flex items-center justify-between flex-wrap gap-2 pt-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Tone:</span>
                  {['Empathetic & Professional', 'Direct & Technical', 'Urgent Action'].map((tone) => (
                    <button
                      key={tone}
                      onClick={() => {
                        setDraftTone(tone);
                        handleGenerateAIResponse(tone);
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
                  onClick={() => handleGenerateAIResponse(draftTone)}
                  disabled={loadingDraft}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-600 to-brand-600 hover:from-blue-500 hover:to-brand-500 text-white shadow-sm disabled:opacity-50"
                  title="Generate a professional customer response"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${loadingDraft ? 'animate-spin' : ''}`} />
                  <span>{loadingDraft ? 'Generating...' : 'Generate AI Response'}</span>
                </button>
              </div>

              {/* Draft Content or Empty Call to Action */}
              {draftResponse || draftBody ? (
                <div className="space-y-3">
                  {isEditingDraft ? (
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                        <span>Edit Customer Response Message:</span>
                        <span className="text-[11px] text-slate-500 font-mono">
                          {editedDraftText.length} characters • {editedDraftText.trim().split(/\s+/).filter(Boolean).length} words
                        </span>
                      </label>
                      <textarea
                        rows={9}
                        value={editedDraftText}
                        onChange={(e) => setEditedDraftText(e.target.value)}
                        className="w-full p-4 rounded-xl bg-slate-950 border border-brand-500/40 text-xs text-slate-100 font-mono leading-relaxed focus:outline-none focus:ring-1 focus:ring-brand-500"
                        placeholder="Enter customer response text..."
                      />
                      <div className="flex items-center gap-2 justify-end">
                        <button
                          onClick={() => {
                            setIsEditingDraft(false);
                            setEditedDraftText(draftResponse?.content || draftBody);
                          }}
                          className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSaveDraftEdit}
                          disabled={savingDraftEdit || !editedDraftText.trim()}
                          className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white transition-all disabled:opacity-50"
                        >
                          <Save className="w-3.5 h-3.5" />
                          <span>{savingDraftEdit ? 'Saving...' : 'Save Draft & Request Approval'}</span>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
                      {draftResponse?.content || draftBody}
                    </div>
                  )}

                  {/* Action Controls: Generate, Edit, Copy, Approve, Send */}
                  <div className="flex items-center justify-between flex-wrap gap-3 pt-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        onClick={() => handleGenerateAIResponse(draftTone)}
                        disabled={loadingDraft || isEditingDraft}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 transition-all disabled:opacity-50"
                      >
                        <Sparkles className={`w-3.5 h-3.5 text-brand-400 ${loadingDraft ? 'animate-spin' : ''}`} />
                        <span>{loadingDraft ? 'Generating...' : 'Generate AI Response'}</span>
                      </button>

                      {!isEditingDraft && (
                        <button
                          onClick={() => {
                            setEditedDraftText(draftResponse?.content || draftBody);
                            setIsEditingDraft(true);
                          }}
                          disabled={draftResponse?.is_sent}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition-all disabled:opacity-40"
                        >
                          <Edit3 className="w-3.5 h-3.5 text-blue-400" />
                          <span>Edit</span>
                        </button>
                      )}

                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(draftResponse?.content || draftBody);
                          setCopied(true);
                          setTimeout(() => setCopied(false), 2000);
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-all"
                      >
                        {copied ? <Check className="w-3.5 h-3.5 text-brand-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
                        <span>{copied ? 'Copied' : 'Copy Text'}</span>
                      </button>
                    </div>

                    <div className="flex items-center gap-2.5 flex-wrap">
                      {/* Approve Button */}
                      {!draftResponse?.is_approved && !draftResponse?.is_sent && (
                        <button
                          onClick={handleApproveDraft}
                          disabled={approvingDraft || isEditingDraft || !draftResponse}
                          className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                          <span>{approvingDraft ? 'Approving...' : 'Approve'}</span>
                        </button>
                      )}

                      {/* Send Button */}
                      <button
                        onClick={handleSendDraft}
                        disabled={!draftResponse?.is_approved || draftResponse?.is_sent || sendingDraft || isEditingDraft}
                        className={`flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-bold transition-all shadow-md ${
                          draftResponse?.is_sent
                            ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700'
                            : draftResponse?.is_approved
                              ? 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-600/25 cursor-pointer'
                              : 'bg-slate-800/80 text-slate-500 border border-slate-700/60 cursor-not-allowed'
                        }`}
                        title={
                          draftResponse?.is_sent
                            ? 'Response has already been sent'
                            : draftResponse?.is_approved
                              ? 'Dispatch this approved response to the customer'
                              : 'Requires explicit human approval before sending'
                        }
                      >
                        <Send className="w-4 h-4" />
                        <span>
                          {sendingDraft
                            ? 'Sending...'
                            : draftResponse?.is_sent
                              ? 'Dispatched'
                              : 'Send'}
                        </span>
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center space-y-4 rounded-xl bg-slate-950/60 border border-dashed border-slate-800 p-6">
                  <div className="p-3 rounded-full bg-blue-500/10 text-blue-400 w-fit mx-auto">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <div className="space-y-1 max-w-md mx-auto">
                    <h4 className="text-sm font-bold text-white">Generate Customer Response</h4>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Click below to let AI compose an empathetic, professional email response formatted with Complaint ID and team sign-off.
                    </p>
                  </div>
                  <button
                    onClick={() => handleGenerateAIResponse(draftTone)}
                    disabled={loadingDraft}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-600 to-brand-600 hover:from-blue-500 hover:to-brand-500 text-white shadow-lg shadow-blue-600/20 transition-all disabled:opacity-50"
                  >
                    <Sparkles className={`w-4 h-4 ${loadingDraft ? 'animate-spin' : ''}`} />
                    <span>{loadingDraft ? 'Drafting response...' : 'Generate AI Response'}</span>
                  </button>
                </div>
              )}
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
