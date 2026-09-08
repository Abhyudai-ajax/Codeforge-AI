'use client';

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Code2,
  Trophy,
  Route,
  BarChart3,
  Users,
  Github,
  Sparkles,
  Brain,
  Settings,
  LogOut,
  Terminal,
  ChevronUp,
} from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { useMySubmissions, useMyLeaderboardStanding } from '@/lib/api/hooks';
import { initialsFor, levelFromPoints } from '@/lib/api/derived';

const WEEKLY_GOAL = 10;
const WEEK_MS = 7 * 24 * 60 * 60 * 1000;

const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);

  const { data: submissions } = useMySubmissions(50);
  const { data: standing } = useMyLeaderboardStanding(isAuthenticated);

  const weeklySolved = useMemo(() => {
    if (!submissions) return 0;
    const cutoff = Date.now() - WEEK_MS;
    return submissions.filter(
      (s) => s.status === 'accepted' && new Date(s.created_at).getTime() >= cutoff
    ).length;
  }, [submissions]);

  const mainNavItems = [
    { href: '/', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/problems', label: 'Problems', icon: Code2, badge: '50' },
    { href: '/roadmaps', label: 'Roadmaps', icon: Route },
    { href: '/contests', label: 'Contests', icon: Trophy },
    { href: '/interviews', label: 'Interviews', icon: Brain },
    { href: '/leaderboard', label: 'Leaderboard', icon: BarChart3 },
    { href: '/rooms', label: 'Rooms', icon: Users },
  ];

  const developerItems = [
    { href: '/github', label: 'GitHub review', icon: Github },
    { href: '/ai-assistant', label: 'AI assistant', icon: Sparkles, dot: true },
  ];

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  const NavRow = ({
    href,
    label,
    icon: Icon,
    badge,
    dot,
  }: {
    href: string;
    label: string;
    icon: React.ElementType;
    badge?: string;
    dot?: boolean;
  }) => (
    <Link href={href}>
      <div
        className={`mb-1 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
          isActive(href)
            ? 'bg-cyan-600/15 text-cyan-300 ring-1 ring-inset ring-cyan-700/50'
            : 'text-gray-400 hover:bg-gray-800/60 hover:text-white'
        }`}
      >
        <Icon size={17} />
        <span className="flex-1 font-medium">{label}</span>
        {badge && (
          <span className="rounded-full bg-gray-800 px-2 py-0.5 text-[11px] font-semibold text-gray-400">
            {badge}
          </span>
        )}
        {dot && <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />}
      </div>
    </Link>
  );

  const weeklyPercent = Math.min(100, Math.round((weeklySolved / WEEKLY_GOAL) * 100));
  const points = standing?.points ?? 0;
  const level = levelFromPoints(points);

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-gray-800/80 bg-black">
      <div className="border-b border-gray-800/80 p-5">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-600 font-bold text-white">
            <Terminal size={16} />
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-bold leading-tight text-white">
              CodeForge <span className="text-cyan-400">AI</span>
            </div>
            <div className="text-[10px] font-medium uppercase tracking-widest text-gray-600">
              Developer Workspace
            </div>
          </div>
        </Link>
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
        <div>
          <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-gray-600">
            Workspace
          </p>
          {mainNavItems.map((item) => (
            <NavRow key={item.href} {...item} />
          ))}
        </div>

        <div>
          <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-gray-600">
            Developer
          </p>
          {developerItems.map((item) => (
            <NavRow key={item.href} {...item} />
          ))}
        </div>
      </div>

      <div className="border-t border-gray-800/80 p-4">
        <div className="mb-4">
          <div className="mb-1.5 flex items-center justify-between text-xs">
            <span className="font-medium text-gray-500">Weekly goal</span>
            <span className="font-semibold text-gray-400">
              {weeklySolved}/{WEEKLY_GOAL}
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500 transition-all"
              style={{ width: `${weeklyPercent}%` }}
            />
          </div>
        </div>

        <div className="relative">
          <button
            onClick={() => setMenuOpen((open) => !open)}
            className="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-gray-800/60"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-600 to-blue-700 text-xs font-bold text-white">
              {initialsFor(user?.full_name, user?.username || 'You')}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">
                {user?.full_name || user?.username || 'Loading...'}
              </p>
              <p className="truncate text-xs text-gray-500">
                Level {level} · {points.toLocaleString()} XP
              </p>
            </div>
            <ChevronUp
              size={16}
              className={`text-gray-600 transition-transform ${menuOpen ? '' : 'rotate-180'}`}
            />
          </button>

          {menuOpen && (
            <div className="absolute bottom-full left-0 mb-2 w-full overflow-hidden rounded-lg border border-gray-800 bg-gray-900 shadow-xl">
              <Link
                href="/settings"
                className="flex items-center gap-2 px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-800 hover:text-white"
                onClick={() => setMenuOpen(false)}
              >
                <Settings size={15} />
                Settings
              </Link>
              <button
                onClick={() => {
                  logout();
                  setMenuOpen(false);
                  router.replace('/login');
                }}
                className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-rose-400 hover:bg-gray-800"
              >
                <LogOut size={15} />
                Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
