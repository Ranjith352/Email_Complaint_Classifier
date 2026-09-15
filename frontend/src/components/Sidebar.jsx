import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Inbox, UserCheck, Building2, Users, Shield,
  BarChart3, Bot, BookOpen, Sparkles, Mail, Bell, FileText, Settings, ShieldCheck, X
} from 'lucide-react';

export default function Sidebar({ isOpen = false, onClose }) {
  const sections = [
    {
      title: 'Operations',
      items: [
        { to: '/', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/complaints', label: 'Complaints Explorer', icon: Inbox },
        { to: '/department-dashboard', label: 'Dept Dashboard', icon: Building2 },
        { to: '/my-assigned', label: 'My Assigned', icon: UserCheck },
        { to: '/departments', label: 'Departments', icon: Building2 },
        { to: '/teams', label: 'Teams', icon: Users },
        { to: '/agents', label: 'Agents', icon: Shield },
      ]
    },
    {
      title: 'Intelligence & RAG',
      items: [
        { to: '/analytics', label: 'Visual Analytics', icon: BarChart3 },
        { to: '/ai-assistant', label: 'AI Policy Assistant', icon: Bot },
        { to: '/knowledge-base', label: 'Knowledge Base', icon: BookOpen },
        { to: '/ai-playground', label: 'AI & RAG Simulator', icon: Sparkles },
      ]
    },
    {
      title: 'System & Ingestion',
      items: [
        { to: '/gmail', label: 'Gmail Ingestion', icon: Mail },
        { to: '/notifications', label: 'Notifications', icon: Bell },
        { to: '/audit-logs', label: 'Audit Logs', icon: FileText },
        { to: '/settings', label: 'Settings', icon: Settings },
      ]
    }
  ];

  const renderNavContent = () => (
    <>
      <div className="space-y-6">
        {sections.map((sec) => (
          <div key={sec.title}>
            <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">{sec.title}</p>
            <nav className="space-y-0.5">
              {sec.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/'}
                    onClick={() => {
                      if (onClose) onClose();
                    }}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                        isActive
                          ? 'bg-gradient-to-r from-brand-600/20 to-emerald-500/10 text-brand-300 border border-brand-500/30 shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                      }`
                    }
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      <div className="pt-4 mt-6 border-t border-slate-800/60">
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-[11px] space-y-1.5">
          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Vector Store</span>
            <span className="font-mono text-emerald-400 font-bold">pgvector</span>
          </div>
          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5"><Bot className="w-3.5 h-3.5 text-blue-400" /> Default LLM</span>
            <span className="font-mono text-blue-400 font-bold">Ollama</span>
          </div>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop static sidebar */}
      <aside className="w-64 border-r border-slate-800/80 bg-slate-950/60 p-4 flex-col justify-between hidden md:flex overflow-y-auto shrink-0">
        {renderNavContent()}
      </aside>

      {/* Mobile Drawer Backdrop and Sidebar */}
      {isOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
            onClick={onClose}
          />

          {/* Drawer Content */}
          <aside className="relative w-72 max-w-[80vw] bg-slate-950 border-r border-slate-800 p-4 flex flex-col justify-between overflow-y-auto z-10 shadow-2xl animate-fade-in">
            <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Navigation Menu</span>
              <button
                onClick={onClose}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                aria-label="Close menu"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            {renderNavContent()}
          </aside>
        </div>
      )}
    </>
  );
}
