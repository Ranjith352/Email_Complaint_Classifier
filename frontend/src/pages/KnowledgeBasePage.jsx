import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Plus,
  ShieldCheck,
  Search,
  FileText,
  Upload,
  Cpu,
  Layers,
  Sparkles,
  RefreshCw,
  Trash2,
  Edit,
  Eye,
  CheckCircle2,
  Database,
  ArrowRight,
  User,
  Building,
  Tag,
  Calendar,
  X
} from 'lucide-react';
import {
  getKnowledgeDocuments,
  getSupportedDocumentTypes,
  getDocumentDetail,
  uploadDocumentFile,
  createKnowledgeDocument,
  updateKnowledgeDocument,
  reindexKnowledgeDocument,
  queryKnowledgeRAG,
  seedKnowledgeBase,
  deleteKnowledgeDocument
} from '../api/knowledge';

export default function KnowledgeBasePage() {
  const [activeTab, setActiveTab] = useState('library'); // 'library' | 'upload' | 'rag'
  const [docs, setDocs] = useState([]);
  const [supportedTypes, setSupportedTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTypeFilter, setSelectedTypeFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Upload Form State
  const [uploadMode, setUploadMode] = useState('file'); // 'file' | 'text'
  const [selectedFile, setSelectedFile] = useState(null);
  const [docName, setDocName] = useState('');
  const [docType, setDocType] = useState('REFUND_POLICY');
  const [docDepartment, setDocDepartment] = useState('Finance');
  const [docCategory, setDocCategory] = useState('Billing / Payment');
  const [docUploadedBy, setDocUploadedBy] = useState('Admin');
  const [docContent, setDocContent] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);

  // Edit / Update Modal State
  const [editingDoc, setEditingDoc] = useState(null);
  const [editName, setEditName] = useState('');
  const [editType, setEditType] = useState('');
  const [editDepartment, setEditDepartment] = useState('');
  const [editContent, setEditContent] = useState('');
  const [updating, setUpdating] = useState(false);

  // View Details Modal State
  const [viewingDoc, setViewingDoc] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Re-indexing State per document
  const [reindexingId, setReindexingId] = useState(null);

  // RAG Playground State
  const [ragQuestion, setRagQuestion] = useState('');
  const [ragLoading, setRagLoading] = useState(false);
  const [ragResult, setRagResult] = useState(null);
  const [ragTypeFilter, setRagTypeFilter] = useState('');

  // Seeding State
  const [seeding, setSeeding] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [docsData, typesData] = await Promise.all([
        getKnowledgeDocuments(),
        getSupportedDocumentTypes().catch(() => [])
      ]);
      setDocs(docsData);
      setSupportedTypes(typesData);
    } catch (err) {
      console.error('Failed to load knowledge base data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const res = await seedKnowledgeBase();
      showNotification(`Successfully seeded ${res.seeded_documents || 9} company knowledge base documents!`);
      await loadData();
    } catch (err) {
      showNotification('Error seeding knowledge base documents.', 'error');
    } finally {
      setSeeding(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to remove "${name}" and its separate chunks and vector embeddings?`)) return;
    try {
      await deleteKnowledgeDocument(id);
      showNotification(`Document "${name}" and its embeddings removed.`);
      loadData();
    } catch (err) {
      showNotification('Failed to delete document.', 'error');
    }
  };

  const handleReindex = async (id, name) => {
    setReindexingId(id);
    try {
      const res = await reindexKnowledgeDocument(id);
      showNotification(`Re-indexed "${name}" successfully! Updated to version v${res.version}.`);
      loadData();
    } catch (err) {
      showNotification('Failed to re-index document.', 'error');
    } finally {
      setReindexingId(null);
    }
  };

  const handleOpenEdit = async (doc) => {
    try {
      const detail = await getDocumentDetail(doc.id);
      setEditingDoc(detail);
      setEditName(detail.title || detail.document_name || '');
      setEditType(detail.document_type || 'REFUND_POLICY');
      setEditDepartment(detail.department || 'General');
      setEditContent(detail.content_text || '');
    } catch (err) {
      showNotification('Failed to load document content for editing.', 'error');
    }
  };

  const handleUpdateSubmit = async (e) => {
    e.preventDefault();
    if (!editingDoc) return;
    setUpdating(true);
    try {
      const res = await updateKnowledgeDocument(editingDoc.id, {
        document_name: editName.trim(),
        title: editName.trim(),
        document_type: editType,
        department: editDepartment,
        content_text: editContent.trim(),
        reindex: true
      });
      showNotification(`Document updated! New version: v${res.version}.`);
      setEditingDoc(null);
      loadData();
    } catch (err) {
      showNotification('Failed to update document.', 'error');
    } finally {
      setUpdating(false);
    }
  };

  const handleOpenView = async (id) => {
    setDetailLoading(true);
    try {
      const detail = await getDocumentDetail(id);
      setViewingDoc(detail);
    } catch (err) {
      showNotification('Failed to load document details.', 'error');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    setUploading(true);
    setUploadSuccess(null);
    try {
      if (uploadMode === 'file') {
        if (!selectedFile) {
          alert('Please select a file to upload (.txt, .md, .json).');
          setUploading(false);
          return;
        }
        const formData = new FormData();
        formData.append('file', selectedFile);
        if (docName.trim()) formData.append('document_name', docName.trim());
        formData.append('document_type', docType);
        formData.append('department', docDepartment);
        formData.append('category', docCategory);
        formData.append('uploaded_by', docUploadedBy || 'Admin');

        const res = await uploadDocumentFile(formData);
        setUploadSuccess(res);
      } else {
        if (!docName.trim() || !docContent.trim()) {
          alert('Please provide document name and content.');
          setUploading(false);
          return;
        }
        const res = await createKnowledgeDocument({
          document_name: docName.trim(),
          title: docName.trim(),
          document_type: docType,
          department: docDepartment,
          category: docCategory,
          uploaded_by: docUploadedBy || 'Admin',
          content_text: docContent.trim()
        });
        setUploadSuccess(res);
      }
      showNotification('Document, chunks, and embeddings indexed separately!');
      setSelectedFile(null);
      setDocName('');
      setDocContent('');
      loadData();
    } catch (err) {
      console.error(err);
      showNotification('Failed to ingest document into knowledge base.', 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleRAGQuery = async (queryText = null) => {
    const q = queryText || ragQuestion;
    if (!q.trim()) return;
    setRagLoading(true);
    setRagResult(null);
    try {
      const res = await queryKnowledgeRAG({
        question: q.trim(),
        document_type: ragTypeFilter || null,
        limit: 4
      });
      setRagResult(res);
    } catch (err) {
      console.error('RAG Query error:', err);
      showNotification('Failed to execute RAG query.', 'error');
    } finally {
      setRagLoading(false);
    }
  };

  const filteredDocs = docs.filter((d) => {
    const matchesType = selectedTypeFilter === 'ALL' || d.document_type === selectedTypeFilter;
    const matchesSearch = !searchQuery.trim() ||
      (d.document_name || d.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (d.department || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (d.uploaded_by || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (d.chunk_text || '').toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  const totalChunks = docs.reduce((acc, curr) => acc + (curr.chunk_count || 1), 0);

  const sampleRAGPrompts = [
    "What is the refund timeline for duplicate card deductions?",
    "What are the SLA response times for Critical P1 complaints?",
    "How should support agents diagnose portal 500 authentication errors?",
    "What is the containment protocol for compromised customer accounts?",
    "Who is authorized to approve goodwill refunds above ₹10,000?"
  ];

  return (
    <div className="space-y-6 pb-12 animate-fade-in text-slate-100">
      {/* Toast Notification */}
      {notification && (
        <div className={`fixed top-5 right-5 z-50 px-4 py-2.5 rounded-xl text-xs font-bold shadow-xl border flex items-center gap-2 animate-slide-in ${
          notification.type === 'error' ? 'bg-rose-950/90 text-rose-200 border-rose-800' : 'bg-emerald-950/90 text-emerald-200 border-emerald-800'
        }`}>
          <CheckCircle2 className="w-4 h-4" />
          <span>{notification.msg}</span>
        </div>
      )}

      {/* Header & Overview Stats */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-brand-500/10 text-brand-400 border border-brand-500/20">
              Admin Knowledge Base & Vector Storage
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-1">
              <Database className="w-3 h-3" /> Chunks & Embeddings Stored Separately
            </span>
          </div>
          <h2 className="text-2xl font-black tracking-tight text-white">Company Knowledge Base Administration</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Manage company policies with versioning, departmental routing, separate chunk/vector tables, and live re-indexing for grounded Ollama/Groq RAG retrieval.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            title="Seed the 9 official enterprise policy documents"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${seeding ? 'animate-spin' : ''}`} />
            <span>{seeding ? 'Seeding Policies...' : 'Seed 9 Policies'}</span>
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-500/20 transition"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Quick Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="glass-panel p-4 rounded-xl border border-slate-800">
          <div className="text-[11px] uppercase tracking-wider font-bold text-slate-400">Total Documents</div>
          <div className="text-2xl font-black text-white mt-1">{docs.length}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Across {supportedTypes.length || 9} Types</div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800">
          <div className="text-[11px] uppercase tracking-wider font-bold text-slate-400">Separate Chunks</div>
          <div className="text-2xl font-black text-brand-400 mt-1">{totalChunks}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Table: knowledge_chunks</div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800">
          <div className="text-[11px] uppercase tracking-wider font-bold text-slate-400">Separate Embeddings</div>
          <div className="text-2xl font-black text-emerald-400 mt-1">{totalChunks}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Table: chunk_embeddings (384-d)</div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800">
          <div className="text-[11px] uppercase tracking-wider font-bold text-slate-400">Admin Actions</div>
          <div className="text-2xl font-black text-purple-400 mt-1">CRUD + Re-index</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Full Version Lifecycle</div>
        </div>
      </div>

      {/* Tabs Switcher */}
      <div className="flex border-b border-slate-800 gap-6 text-xs font-bold">
        <button
          onClick={() => setActiveTab('library')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition ${
            activeTab === 'library'
              ? 'border-brand-500 text-brand-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Documents Directory ({docs.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('rag')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition ${
            activeTab === 'rag'
              ? 'border-purple-500 text-purple-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>RAG Q&A Playground</span>
        </button>
        <button
          onClick={() => setActiveTab('upload')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition ${
            activeTab === 'upload'
              ? 'border-brand-500 text-brand-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Upload className="w-4 h-4" />
          <span>Upload Document</span>
        </button>
      </div>

      {/* TAB 1: DOCUMENTS DIRECTORY */}
      {activeTab === 'library' && (
        <div className="space-y-4">
          {/* Filters & Search */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="relative w-full sm:w-80">
              <Search className="w-3.5 h-3.5 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search document name, department, author..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>

            <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
              <button
                onClick={() => setSelectedTypeFilter('ALL')}
                className={`px-3 py-1.5 rounded-lg text-[11px] font-bold whitespace-nowrap transition ${
                  selectedTypeFilter === 'ALL'
                    ? 'bg-brand-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
                }`}
              >
                All Documents
              </button>
              {supportedTypes.map((t) => (
                <button
                  key={t.type}
                  onClick={() => setSelectedTypeFilter(t.type)}
                  className={`px-3 py-1.5 rounded-lg text-[11px] font-bold whitespace-nowrap transition ${
                    selectedTypeFilter === t.type
                      ? 'bg-brand-600 text-white'
                      : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  {t.name}
                </button>
              ))}
            </div>
          </div>

          {/* Documents Grid */}
          {loading ? (
            <div className="glass-panel p-12 text-center text-xs text-slate-400">Loading knowledge base...</div>
          ) : filteredDocs.length === 0 ? (
            <div className="glass-panel p-12 text-center space-y-3 rounded-2xl border border-slate-800">
              <BookOpen className="w-10 h-10 mx-auto text-slate-600" />
              <div className="text-sm font-bold text-white">No Policy Documents Found</div>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                No documents match the active filter. Click "Seed 9 Policies" to initialize the official enterprise policies.
              </p>
              <button
                onClick={handleSeed}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white"
              >
                Seed Default Knowledge Base
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDocs.map((d) => (
                <div key={d.id} className="glass-panel p-5 rounded-2xl border border-slate-800/90 hover:border-slate-700/80 transition flex flex-col justify-between space-y-3">
                  <div className="space-y-2">
                    {/* Header Badges */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <span className="text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20">
                        {d.document_type.replace('_', ' ')}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-brand-500/15 text-brand-300 border border-brand-500/30">
                          v{d.version || 1}
                        </span>
                        <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                          <Layers className="w-3 h-3" /> {d.chunk_count || 1} Chunks
                        </span>
                      </div>
                    </div>

                    {/* Document Name */}
                    <h3 className="text-sm font-bold text-white line-clamp-1">
                      {d.document_name || d.title}
                    </h3>

                    {/* Meta fields required: department, uploaded_by, created_at */}
                    <div className="grid grid-cols-2 gap-1.5 text-[10px] text-slate-400 bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                      <div className="flex items-center gap-1">
                        <Building className="w-3 h-3 text-slate-500" />
                        <span className="truncate">{d.department || 'General'}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3 text-slate-500" />
                        <span className="truncate">{d.uploaded_by || 'Admin'}</span>
                      </div>
                      <div className="flex items-center gap-1 col-span-2 text-slate-500">
                        <Calendar className="w-3 h-3" />
                        <span>{new Date(d.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    {/* Snippet Preview */}
                    <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/70 p-3 rounded-xl border border-slate-900 line-clamp-3 font-mono text-[11px]">
                      {d.chunk_text}
                    </p>
                  </div>

                  {/* Actions Bar: View, Edit, Re-index, Delete */}
                  <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between gap-1 text-[11px]">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleOpenView(d.id)}
                        className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 transition"
                        title="View Document & Chunks"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleOpenEdit(d)}
                        className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-brand-400 transition"
                        title="Update Document"
                      >
                        <Edit className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleReindex(d.id, d.document_name || d.title)}
                        disabled={reindexingId === d.id}
                        className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-purple-400 transition disabled:opacity-50"
                        title="Re-index Chunks & Embeddings"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${reindexingId === d.id ? 'animate-spin' : ''}`} />
                      </button>
                    </div>

                    <button
                      onClick={() => handleDelete(d.id, d.document_name || d.title)}
                      className="p-1.5 rounded-lg bg-slate-900 hover:bg-rose-950/40 text-slate-500 hover:text-rose-400 transition"
                      title="Delete document and separate vectors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* EDIT DOCUMENT MODAL */}
      {editingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="glass-panel p-6 rounded-2xl border border-brand-500/40 max-w-2xl w-full max-h-[90vh] overflow-y-auto space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Edit className="w-4 h-4 text-brand-400" />
                Update Document: {editingDoc.title} (Current: v{editingDoc.version})
              </h3>
              <button
                onClick={() => setEditingDoc(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUpdateSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">
                    Document Name
                  </label>
                  <input
                    type="text"
                    required
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">
                    Department
                  </label>
                  <input
                    type="text"
                    required
                    value={editDepartment}
                    onChange={(e) => setEditDepartment(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">
                    Document Type
                  </label>
                  <select
                    value={editType}
                    onChange={(e) => setEditType(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                  >
                    {supportedTypes.map((t) => (
                      <option key={t.type} value={t.type}>{t.name} ({t.category})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">
                  Document Content (Markdown)
                </label>
                <textarea
                  rows={8}
                  required
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white font-mono leading-relaxed focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="text-[11px] text-slate-400 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                Updating content automatically re-indexes separate chunks & embeddings and increments version to <strong>v{editingDoc.version + 1}</strong>.
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingDoc(null)}
                  className="px-4 py-2 rounded-xl text-xs bg-slate-800 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updating}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white flex items-center gap-2"
                >
                  {updating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                  <span>{updating ? 'Saving & Re-indexing...' : 'Save & Bump Version'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* VIEW DOCUMENT & CHUNKS MODAL */}
      {viewingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="glass-panel p-6 rounded-2xl border border-brand-500/40 max-w-3xl w-full max-h-[90vh] overflow-y-auto space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20">
                  {viewingDoc.document_type} • v{viewingDoc.version}
                </span>
                <h3 className="text-base font-bold text-white mt-1">
                  {viewingDoc.document_name || viewingDoc.title}
                </h3>
              </div>
              <button
                onClick={() => setViewingDoc(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs text-slate-300 bg-slate-900 p-3 rounded-xl border border-slate-800">
              <div><span className="text-slate-500">Department:</span> {viewingDoc.department}</div>
              <div><span className="text-slate-500">Uploaded By:</span> {viewingDoc.uploaded_by}</div>
              <div><span className="text-slate-500">Created:</span> {new Date(viewingDoc.created_at).toLocaleDateString()}</div>
            </div>

            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-brand-400" />
                Separately Stored Chunks ({viewingDoc.chunks?.length || 0})
              </h4>
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {viewingDoc.chunks?.map((c) => (
                  <div key={c.id} className="bg-slate-950 p-3 rounded-xl border border-slate-900 text-xs space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span>Chunk #{c.chunk_index} ({c.token_count} tokens)</span>
                      <span className="text-emerald-400 font-mono">Embedding: 384-d vector</span>
                    </div>
                    <p className="text-slate-300 font-mono text-[11px] leading-relaxed">{c.chunk_text}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setViewingDoc(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 text-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: RAG Q&A PLAYGROUND */}
      {activeTab === 'rag' && (
        <div className="space-y-6 animate-fade-in">
          <div className="glass-panel p-6 rounded-2xl border border-purple-500/30 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-black text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  RAG Question Answering Studio
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Semantic retrieval over separately stored pgvector embeddings followed by grounded answer generation via Ollama / Groq.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={ragTypeFilter}
                  onChange={(e) => setRagTypeFilter(e.target.value)}
                  className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none"
                >
                  <option value="">All Document Types</option>
                  {supportedTypes.map((t) => (
                    <option key={t.type} value={t.type}>{t.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={ragQuestion}
                onChange={(e) => setRagQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleRAGQuery()}
                placeholder="Ask any policy question (e.g. 'What is the refund timeline for duplicate charges?')..."
                className="flex-1 bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-3 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-500"
              />
              <button
                onClick={() => handleRAGQuery()}
                disabled={ragLoading || !ragQuestion.trim()}
                className="px-6 py-3 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white shadow-lg shadow-purple-500/20 transition flex items-center gap-2"
              >
                {ragLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                <span>{ragLoading ? 'Retrieving...' : 'Ask Knowledge Base'}</span>
              </button>
            </div>

            {/* Quick Sample Chips */}
            <div className="flex items-center gap-2 flex-wrap pt-1">
              <span className="text-[11px] text-slate-500 font-bold">Try asking:</span>
              {sampleRAGPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setRagQuestion(prompt);
                    handleRAGQuery(prompt);
                  }}
                  className="text-[10px] px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          {/* RAG Answer Display */}
          {ragResult && (
            <div className="space-y-6 animate-fade-in">
              <div className="glass-panel p-6 rounded-2xl border border-emerald-500/40 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" /> Grounded RAG Answer
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    Provider: <strong className="text-purple-400">{ragResult.provider}</strong>
                  </span>
                </div>

                <div className="text-sm text-slate-100 leading-relaxed bg-slate-950/80 p-4 rounded-xl border border-slate-900 whitespace-pre-line font-sans">
                  {ragResult.answer}
                </div>
              </div>

              {/* Cited Granular Chunks */}
              <div className="space-y-3">
                <h4 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <Database className="w-3.5 h-3.5 text-brand-400" />
                  Retrieved Policy Context & Cited Chunks ({ragResult.cited_chunks?.length || 0})
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {ragResult.cited_chunks?.map((chunk, idx) => (
                    <div key={idx} className="glass-panel p-4 rounded-xl border border-slate-800/80 space-y-2">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="font-bold text-white">{chunk.document_title}</span>
                        <span className="text-emerald-400 font-mono font-bold">
                          Similarity: {(chunk.similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="text-[10px] text-purple-400 font-mono">
                        {chunk.document_type} • Dept: {chunk.department || 'General'} • Chunk #{chunk.chunk_index}
                      </div>
                      <p className="text-xs text-slate-300 bg-slate-950/60 p-2.5 rounded-lg border border-slate-900 leading-relaxed font-mono text-[11px]">
                        {chunk.chunk_text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: UPLOAD DOCUMENT STUDIO */}
      {activeTab === 'upload' && (
        <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
          <div className="glass-panel p-6 rounded-2xl border border-brand-500/30 space-y-5">
            <div>
              <h3 className="text-sm font-black text-white flex items-center gap-2">
                <Upload className="w-4 h-4 text-brand-400" />
                Upload & Ingest Enterprise Document
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Upload policy files or author markdown text to store Document metadata, Chunks, and Vector Embeddings in separate tables.
              </p>
            </div>

            {/* Ingestion Mode Toggle */}
            <div className="flex rounded-xl bg-slate-900 p-1 border border-slate-800 text-xs font-bold max-w-xs">
              <button
                type="button"
                onClick={() => setUploadMode('file')}
                className={`flex-1 py-1.5 rounded-lg transition ${
                  uploadMode === 'file' ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Upload File (.txt, .md, .json)
              </button>
              <button
                type="button"
                onClick={() => setUploadMode('text')}
                className={`flex-1 py-1.5 rounded-lg transition ${
                  uploadMode === 'text' ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Author Direct Text
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">
                    Document Name (Optional for file upload)
                  </label>
                  <input
                    type="text"
                    value={docName}
                    onChange={(e) => setDocName(e.target.value)}
                    placeholder="e.g. Executive Chargeback Governance"
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">
                    Department
                  </label>
                  <input
                    type="text"
                    value={docDepartment}
                    onChange={(e) => setDocDepartment(e.target.value)}
                    placeholder="e.g. Finance, IT Support, Security"
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">
                    Document Type
                  </label>
                  <select
                    value={docType}
                    onChange={(e) => {
                      setDocType(e.target.value);
                      const matched = supportedTypes.find((s) => s.type === e.target.value);
                      if (matched) {
                        setDocCategory(matched.category);
                        setDocDepartment(matched.department);
                      }
                    }}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"
                  >
                    {supportedTypes.map((t) => (
                      <option key={t.type} value={t.type}>
                        {t.name} ({t.category})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">
                    Uploaded By
                  </label>
                  <input
                    type="text"
                    value={docUploadedBy}
                    onChange={(e) => setDocUploadedBy(e.target.value)}
                    placeholder="Admin, System Lead, etc."
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              {uploadMode === 'file' ? (
                <div className="border-2 border-dashed border-slate-800 hover:border-brand-500/50 rounded-2xl p-8 text-center space-y-3 transition bg-slate-900/40">
                  <FileText className="w-10 h-10 mx-auto text-brand-400/80" />
                  <div className="text-xs text-slate-300 font-bold">
                    {selectedFile ? selectedFile.name : 'Select or drag & drop a policy document'}
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Supports plain text, markdown (.md), JSON, and standard documentation formats.
                  </p>
                  <label className="inline-block px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white cursor-pointer border border-slate-700 transition">
                    Browse File
                    <input
                      type="file"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          setSelectedFile(e.target.files[0]);
                          if (!docName) {
                            setDocName(e.target.files[0].name.split('.')[0].replace(/_/g, ' '));
                          }
                        }
                      }}
                    />
                  </label>
                </div>
              ) : (
                <div>
                  <label className="block text-[10px] uppercase text-slate-400 font-bold mb-1">
                    Policy Document Content (Markdown Supported)
                  </label>
                  <textarea
                    rows={8}
                    required
                    value={docContent}
                    onChange={(e) => setDocContent(e.target.value)}
                    placeholder="# Section 1: Scope&#10;All customer refund requests submitted within 30 days..."
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white font-mono leading-relaxed placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              )}

              {/* Separation Architecture Callout */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-900 space-y-2">
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                  Separate Relational Storage Architecture:
                </span>
                <div className="grid grid-cols-3 gap-2 text-[11px] font-mono">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <strong className="text-brand-300 block">1. knowledge_documents</strong>
                    <span className="text-[10px] text-slate-400">Name, Type, Dept, Version, Author</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <strong className="text-purple-300 block">2. knowledge_chunks</strong>
                    <span className="text-[10px] text-slate-400">Granular text chunks & indices</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <strong className="text-emerald-300 block">3. chunk_embeddings</strong>
                    <span className="text-[10px] text-slate-400">384-d dense vectors for pgvector</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-6 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white shadow-lg shadow-brand-500/20 transition flex items-center gap-2"
                >
                  {uploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  <span>{uploading ? 'Ingesting Document...' : 'Upload & Index Separately'}</span>
                </button>
              </div>
            </form>

            {uploadSuccess && (
              <div className="bg-emerald-950/40 border border-emerald-800/60 p-4 rounded-xl text-xs text-emerald-200 space-y-1">
                <div className="font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Document "{uploadSuccess.document_name || uploadSuccess.title}" Ingested Successfully!
                </div>
                <div className="text-[11px] text-emerald-300/80">
                  Version: v{uploadSuccess.version} • Dept: {uploadSuccess.department} • Uploaded By: {uploadSuccess.uploaded_by} • Chunks: {uploadSuccess.chunk_count}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
