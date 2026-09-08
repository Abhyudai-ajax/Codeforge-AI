'use client';

import React, { useState } from 'react';
import { RankBadge, UserAvatar, Spinner, EmptyState } from './SharedComponents';
import { useLeaderboard, useMyLeaderboardStanding } from '@/lib/api/hooks';
import { useAuthStore } from '@/store/auth';

const PAGE_SIZE = 20;

const GlobalLeaderboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const [offset, setOffset] = useState(0);
  const { data, isLoading } = useLeaderboard({ offset, limit: PAGE_SIZE });
  const { data: myStanding } = useMyLeaderboardStanding(true);

  const items = data?.items ?? [];
  const podium = offset === 0 ? items.slice(0, 3) : [];
  const rest = offset === 0 ? items.slice(3) : items;
  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const page = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="min-h-full bg-[#0B0F17] p-6">
      <div className="mx-auto max-w-5xl space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Leaderboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Ranked by difficulty-weighted points — easy 10, medium 30, hard 50.
          </p>
        </div>

        {isLoading ? (
          <div className="flex h-40 items-center justify-center">
            <Spinner />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            title="No one has solved a problem yet"
            description="Be the first to appear on the leaderboard."
          />
        ) : (
          <>
            {podium.length > 0 && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {[podium[1], podium[0], podium[2]].map((entry, index) =>
                  entry ? (
                    <div
                      key={entry.user_id}
                      className={`flex flex-col items-center rounded-lg border p-6 ${
                        index === 1
                          ? 'border-amber-600/60 bg-gradient-to-b from-amber-900/20 to-gray-900/60 sm:order-2'
                          : `border-gray-800 bg-gray-900/60 ${index === 0 ? 'sm:order-1' : 'sm:order-3'}`
                      }`}
                    >
                      <RankBadge rank={entry.rank} />
                      <div className="mt-3">
                        <UserAvatar
                          name={entry.full_name || entry.username}
                          avatarUrl={entry.avatar_url}
                          size="lg"
                        />
                      </div>
                      <h3 className="mt-3 text-base font-bold text-white">
                        {entry.full_name || entry.username}
                      </h3>
                      <p className="text-sm text-gray-500">@{entry.username}</p>
                      <div className="mt-4 grid w-full grid-cols-2 gap-3 border-t border-gray-800 pt-4 text-center">
                        <div>
                          <p className="text-[11px] uppercase text-gray-500">Solved</p>
                          <p className="text-lg font-bold text-white">{entry.solved_count}</p>
                        </div>
                        <div>
                          <p className="text-[11px] uppercase text-gray-500">Points</p>
                          <p className="text-lg font-bold text-cyan-400">
                            {entry.points.toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div key={index} />
                  )
                )}
              </div>
            )}

            <div className="overflow-hidden rounded-lg border border-gray-800 bg-gray-900/60">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    <th className="px-5 py-3">Rank</th>
                    <th className="px-3 py-3">User</th>
                    <th className="px-3 py-3 text-center">Solved</th>
                    <th className="px-3 py-3 text-right">Points</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/70">
                  {rest.map((entry) => (
                    <tr
                      key={entry.user_id}
                      className={`transition-colors hover:bg-gray-800/40 ${
                        entry.username === user?.username ? 'bg-cyan-950/20' : ''
                      }`}
                    >
                      <td className="px-5 py-3 font-mono text-sm text-gray-400">#{entry.rank}</td>
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-3">
                          <UserAvatar
                            name={entry.full_name || entry.username}
                            avatarUrl={entry.avatar_url}
                            size="sm"
                          />
                          <span className="text-sm font-medium text-gray-200">
                            {entry.full_name || entry.username}
                            {entry.username === user?.username && (
                              <span className="ml-2 text-xs text-cyan-400">(you)</span>
                            )}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-3 text-center text-sm text-gray-400">
                        {entry.solved_count}
                      </td>
                      <td className="px-3 py-3 text-right text-sm font-semibold text-gray-300">
                        {entry.points.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {pageCount > 1 && (
              <div className="flex items-center justify-between text-sm">
                <button
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                  disabled={offset === 0}
                  className="rounded-lg bg-gray-900/70 px-4 py-2 font-medium text-gray-300 hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="text-gray-500">
                  Page {page} of {pageCount}
                </span>
                <button
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                  disabled={page >= pageCount}
                  className="rounded-lg bg-gray-900/70 px-4 py-2 font-medium text-gray-300 hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}

        {myStanding && myStanding.rank && myStanding.rank > offset + items.length && (
          <div className="sticky bottom-4 flex items-center gap-3 rounded-lg border border-cyan-800/50 bg-gray-900/95 px-5 py-3 shadow-xl">
            <span className="font-mono text-sm text-cyan-400">#{myStanding.rank}</span>
            <span className="text-sm font-medium text-cyan-300">Your standing</span>
            <span className="ml-auto text-sm font-semibold text-gray-300">
              {myStanding.solved_count} solved · {myStanding.points.toLocaleString()} pts
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default GlobalLeaderboardPage;
