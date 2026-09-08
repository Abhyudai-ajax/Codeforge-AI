'use client';

import React from 'react';
import { difficultyColor, formatStatusLabel, statusColor } from '@/lib/api/derived';
import type { Difficulty, SubmissionStatus } from '@/lib/api/types';

export const DifficultyBadge: React.FC<{ difficulty: Difficulty | string; className?: string }> = ({
  difficulty,
  className = '',
}) => (
  <span
    className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${difficultyColor(difficulty)} ${className}`}
  >
    {difficulty}
  </span>
);

export const UserAvatar: React.FC<{
  name: string;
  avatarUrl?: string | null;
  size?: 'sm' | 'md' | 'lg';
}> = ({ name, avatarUrl, size = 'md' }) => {
  const sizeClasses = { sm: 'w-8 h-8 text-xs', md: 'w-11 h-11 text-sm', lg: 'w-16 h-16 text-lg' };
  const initials = name
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div
      className={`${sizeClasses[size]} flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-cyan-600 to-blue-700 font-bold text-white`}
    >
      {avatarUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={avatarUrl} alt={name} className="h-full w-full object-cover" />
      ) : (
        initials || '?'
      )}
    </div>
  );
};

export const Button: React.FC<{
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}> = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  className = '',
  type = 'button',
}) => {
  const baseClasses =
    'font-medium rounded-lg transition-colors flex items-center gap-2 justify-center disabled:cursor-not-allowed';
  const variantClasses = {
    primary: 'bg-cyan-600 hover:bg-cyan-500 text-white disabled:bg-gray-800 disabled:text-gray-500',
    secondary:
      'bg-gray-800 hover:bg-gray-700 text-gray-200 disabled:bg-gray-900 disabled:text-gray-600',
    danger: 'bg-rose-600 hover:bg-rose-500 text-white disabled:bg-gray-800',
    success: 'bg-emerald-600 hover:bg-emerald-500 text-white disabled:bg-gray-800',
  };
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-base',
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {children}
    </button>
  );
};

export const StatusBadge: React.FC<{ status: SubmissionStatus | string }> = ({ status }) => (
  <span
    className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold ${statusColor(status)}`}
  >
    {formatStatusLabel(status)}
  </span>
);

export const StatCard: React.FC<{
  label: string;
  value: string | number;
  unit?: string;
  comparison?: string;
  color?: 'cyan' | 'emerald' | 'amber' | 'rose';
}> = ({ label, value, unit, comparison, color = 'cyan' }) => {
  const colorClasses = {
    cyan: 'text-cyan-400',
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
    rose: 'text-rose-400',
  };
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-4">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">{label}</p>
      <div className="flex items-baseline gap-2">
        <span className={`text-2xl font-bold ${colorClasses[color]}`}>{value}</span>
        {unit && <span className="text-sm text-gray-500">{unit}</span>}
      </div>
      {comparison && <p className={`mt-2 text-xs ${colorClasses[color]}`}>{comparison}</p>}
    </div>
  );
};

export const Tabs: React.FC<{
  tabs: { label: string; value: string; content: React.ReactNode }[];
  defaultTab?: string;
  onChange?: (tab: string) => void;
}> = ({ tabs, defaultTab = tabs[0]?.value, onChange }) => {
  const [activeTab, setActiveTab] = React.useState(defaultTab);
  const handleChange = (tab: string) => {
    setActiveTab(tab);
    onChange?.(tab);
  };
  return (
    <div className="w-full">
      <div className="mb-6 flex gap-4 border-b border-gray-800">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => handleChange(tab.value)}
            className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.value
                ? 'border-cyan-500 text-cyan-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div>{tabs.find((tab) => tab.value === activeTab)?.content}</div>
    </div>
  );
};

export const EmptyState: React.FC<{
  title: string;
  description?: string;
  action?: React.ReactNode;
}> = ({ title, description, action }) => (
  <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-800 py-12 text-center">
    <p className="text-sm font-medium text-gray-300">{title}</p>
    {description && <p className="mt-1 max-w-sm text-xs text-gray-500">{description}</p>}
    {action && <div className="mt-4">{action}</div>}
  </div>
);

export const RankBadge: React.FC<{ rank: number }> = ({ rank }) => {
  const medals: Record<number, string> = { 1: '🥇', 2: '🥈', 3: '🥉' };
  if (!medals[rank]) return <span className="font-mono text-sm text-gray-500">#{rank}</span>;
  return <span className="text-xl">{medals[rank]}</span>;
};

export const Spinner: React.FC<{ size?: number }> = ({ size = 20 }) => (
  <div
    className="animate-spin rounded-full border-2 border-gray-700 border-t-cyan-500"
    style={{ width: size, height: size }}
  />
);
