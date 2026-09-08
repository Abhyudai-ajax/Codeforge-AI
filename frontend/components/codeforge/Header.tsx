'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Search, Bell, ArrowUpRight, Circle } from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import {
  useBackendHealth,
  useCommandK,
  useDebouncedValue,
  useMarkAllNotificationsRead,
  useNotifications,
  useUnreadNotificationCount,
} from '@/lib/api/hooks';
import { problemsApi } from '@/lib/api/endpoints';
import type { ProblemListItem } from '@/lib/api/types';
import { initialsFor, difficultyColor } from '@/lib/api/derived';

function useLiveSearch(query: string) {
  const debounced = useDebouncedValue(query, 250);
  const [results, setResults] = useState<ProblemListItem[]>([]);
  useEffect(() => {
    let cancelled = false;
    if (!debounced.trim()) {
      setResults([]);
      return;
    }
    problemsApi
      .list({ search: debounced, limit: 6 })
      .then((page) => {
        if (!cancelled) setResults(page.items);
      })
      .catch(() => {
        if (!cancelled) setResults([]);
      });
    return () => {
      cancelled = true;
    };
  }, [debounced]);
  return results;
}

const Header: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchResults = useLiveSearch(searchQuery);

  const { data: health, isError: healthDown } = useBackendHealth();
  const { data: unread } = useUnreadNotificationCount(isAuthenticated);
  const { data: notifications } = useNotifications(notifOpen && isAuthenticated);
  const markAllRead = useMarkAllNotificationsRead();

  useCommandK(() => {
    setSearchOpen(true);
    setTimeout(() => searchInputRef.current?.focus(), 0);
  });

  const breadcrumb = pathname === '/' ? 'dashboard' : pathname.replace(/^\//, '').split('/')[0];
  const isLive = health !== undefined && !healthDown;

  const goToProblem = (problem: ProblemListItem) => {
    setSearchQuery('');
    setSearchOpen(false);
    router.push(`/problems/${problem.id}`);
  };

  return (
    <header className="border-b border-gray-800/80 bg-black px-8 py-3.5">
      <div className="flex items-center gap-4">
        <div className="hidden shrink-0 items-center gap-2 font-mono text-xs text-gray-600 lg:flex">
          <span className="text-gray-700">⌘</span>
          <span>~/{breadcrumb.toUpperCase()}</span>
          <span className="text-gray-700">•</span>
          <span className="flex items-center gap-1 text-cyan-500">
            <Circle size={6} className="animate-pulse-subtle fill-cyan-500" />
            LIVE
          </span>
        </div>

        <div className="relative flex-1 max-w-xl">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-600"
            size={16}
          />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setSearchOpen(true)}
            onBlur={() => setTimeout(() => setSearchOpen(false), 150)}
            placeholder="Search problems, rooms, or commands..."
            className="w-full rounded-lg border border-gray-800 bg-gray-900/70 py-2 pl-9 pr-14 text-sm text-white placeholder-gray-600 focus:border-cyan-700 focus:outline-none focus:ring-1 focus:ring-cyan-700"
          />
          <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded border border-gray-700 bg-gray-800 px-1.5 py-0.5 font-mono text-[10px] text-gray-500">
            ⌘K
          </kbd>

          {searchOpen && searchQuery.trim() && (
            <div className="absolute left-0 right-0 top-full z-30 mt-2 overflow-hidden rounded-lg border border-gray-800 bg-gray-900 shadow-2xl">
              {searchResults.length === 0 ? (
                <p className="px-4 py-3 text-sm text-gray-500">
                  No problems match &ldquo;{searchQuery}&rdquo;.
                </p>
              ) : (
                searchResults.map((problem) => (
                  <button
                    key={problem.id}
                    onMouseDown={() => goToProblem(problem)}
                    className="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left text-sm hover:bg-gray-800"
                  >
                    <span className="truncate text-gray-200">{problem.title}</span>
                    <span
                      className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase ${difficultyColor(problem.difficulty)}`}
                    >
                      {problem.difficulty}
                    </span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-1.5 rounded-full border border-gray-800 bg-gray-900/70 px-3 py-1.5 text-xs font-medium text-gray-400 md:flex">
            <Circle
              size={7}
              className={`${isLive ? 'fill-emerald-500 text-emerald-500' : 'fill-rose-500 text-rose-500'}`}
            />
            {isLive ? 'all systems operational' : 'backend unreachable'}
          </div>

          <div className="relative">
            <button
              onClick={() => setNotifOpen((open) => !open)}
              className="relative rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-800 hover:text-white"
            >
              <Bell size={18} />
              {!!unread?.unread_count && (
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-black" />
              )}
            </button>
            {notifOpen && (
              <div className="absolute right-0 top-full z-30 mt-2 w-80 overflow-hidden rounded-lg border border-gray-800 bg-gray-900 shadow-2xl">
                <div className="flex items-center justify-between border-b border-gray-800 px-4 py-3">
                  <span className="text-sm font-semibold text-white">Notifications</span>
                  {!!unread?.unread_count && (
                    <button
                      onClick={() => markAllRead.mutate()}
                      className="text-xs font-medium text-cyan-400 hover:text-cyan-300"
                    >
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {!notifications || notifications.length === 0 ? (
                    <p className="px-4 py-6 text-center text-sm text-gray-500">
                      You&apos;re all caught up.
                    </p>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`border-b border-gray-800/60 px-4 py-3 ${n.is_read ? 'opacity-60' : ''}`}
                      >
                        <p className="text-sm font-medium text-gray-200">{n.title}</p>
                        <p className="mt-0.5 text-xs text-gray-500">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <Link
            href="/problems"
            className="flex items-center gap-1.5 rounded-lg bg-cyan-600 px-3.5 py-2 text-sm font-semibold text-white transition-colors hover:bg-cyan-500"
          >
            Open workspace
            <ArrowUpRight size={15} />
          </Link>

          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-600 to-blue-700 text-xs font-bold text-white">
            {initialsFor(user?.full_name, user?.username || '?')}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
