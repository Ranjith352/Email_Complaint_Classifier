import React from 'react';
import { CreditCard, Server, ShieldAlert, Headphones, Briefcase } from 'lucide-react';

export default function DepartmentBadge({ department }) {
  const dept = (department || '').toLowerCase();

  if (dept.includes('finance')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
        <CreditCard className="w-3.5 h-3.5" />
        Finance & Billing
      </span>
    );
  }
  if (dept.includes('it') || dept.includes('infra')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-blue-500/10 text-blue-300 border border-blue-500/20">
        <Server className="w-3.5 h-3.5" />
        IT & Systems
      </span>
    );
  }
  if (dept.includes('security')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">
        <ShieldAlert className="w-3.5 h-3.5" />
        Security & Ops
      </span>
    );
  }
  if (dept.includes('operation') || dept.includes('admin')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
        <Briefcase className="w-3.5 h-3.5" />
        Operations
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-500/10 text-slate-300 border border-slate-500/20">
      <Headphones className="w-3.5 h-3.5" />
      Support
    </span>
  );
}
