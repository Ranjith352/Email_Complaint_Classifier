import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend
} from 'recharts';

const PRIORITY_COLORS = {
  'P1': '#ef4444',
  'Critical': '#ef4444',
  'P2': '#f97316',
  'High': '#f97316',
  'P3': '#eab308',
  'Medium': '#eab308',
  'P4': '#3b82f6',
  'Low': '#3b82f6'
};

export default function PriorityDistributionChart({ data = [], height = 280 }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 text-sm">
        No priority data
      </div>
    );
  }

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip
            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem' }}
          />
          <Legend wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
          <Pie
            data={data}
            dataKey="count"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            paddingAngle={3}
          >
            {data.map((entry, index) => {
              const color = PRIORITY_COLORS[entry.name] || '#64748b';
              return <Cell key={`cell-${index}`} fill={color} />;
            })}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
