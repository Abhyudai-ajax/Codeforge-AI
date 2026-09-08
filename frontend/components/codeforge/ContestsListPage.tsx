'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Trophy, Users, Clock } from 'lucide-react';
import { Spinner, EmptyState } from './SharedComponents';
import { useContests } from '@/lib/api/hooks';
import type { ContestStatus } from '@/lib/api/types';

const STATUS_STYLE: Record<ContestStatus, string> = {
  upcoming: 'text-cyan-400 border-cyan-700 bg-cyan-900/30',
  running: 'text-emerald-400 border-emerald-700 bg-emerald-900/30',
  ended: 'text-gray-500 border-gray-700 bg-gray-900/30',
};

const ContestsListPage: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<ContestStatus | undefined>();
  const { data: contests, isLoading } = useContests({ status: statusFilter });

  return (
    <div className="min-h-full space-y-6 bg-[#0B0F17] p-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold text-white">
          <Trophy size={22} className="text-amber-400" />
          Contests
        </h1>
        <p className="mt-1 text-sm text-gray-500">Timed challenges with a live leaderboard.</p>
      </div>

      <div className="flex gap-2">
        {(['upcoming', 'running', 'ended'] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(statusFilter === s ? undefined : s)}
            className={`rounded-lg px-3.5 py-2 text-sm font-medium capitalize transition-colors ${
              statusFilter === s
                ? 'bg-cyan-600 text-white'
                : 'bg-gray-900/70 text-gray-400 hover:bg-gray-800'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex h-40 items-center justify-center">
          <Spinner />
        </div>
      ) : !contests || contests.length === 0 ? (
        <EmptyState
          title="No contests found"
          description="Check back later for scheduled contests."
        />
      ) : (
        <div className="space-y-3">
          {contests.map((contest) => (
            <Link
              key={contest.id}
              href={`/contests/${contest.id}`}
              className="flex items-center gap-4 rounded-lg border border-gray-800 bg-gray-900/60 p-5 transition-colors hover:bg-gray-800/50"
            >
              <div className="min-w-0 flex-1">
                <div className="mb-1.5 flex items-center gap-2">
                  <h3 className="font-semibold text-white">{contest.title}</h3>
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase ${STATUS_STYLE[contest.status]}`}
                  >
                    {contest.status}
                  </span>
                  {contest.is_registered && (
                    <span className="rounded-full border border-cyan-700 bg-cyan-900/30 px-2 py-0.5 text-[10px] font-semibold text-cyan-400">
                      Registered
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <Clock size={12} />
                    {new Date(contest.start_time).toLocaleString()} →{' '}
                    {new Date(contest.end_time).toLocaleString()}
                  </span>
                  <span className="flex items-center gap-1">
                    <Users size={12} />
                    {contest.participant_count} registered
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContestsListPage;
