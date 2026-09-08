'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Search, CheckCircle2 } from 'lucide-react';
import { DifficultyBadge, Spinner } from './SharedComponents';
import { useDebouncedValue, useProblems, useProgressByProblem } from '@/lib/api/hooks';
import { useAuthStore } from '@/store/auth';

const DIFFICULTIES = ['easy', 'medium', 'hard'] as const;
const PAGE_SIZE = 20;

const ProblemsListPage: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const [search, setSearch] = useState('');
  const [difficulty, setDifficulty] = useState<string | undefined>();
  const [offset, setOffset] = useState(0);

  const debouncedSearch = useDebouncedValue(search, 300);
  const { data, isLoading } = useProblems({
    search: debouncedSearch || undefined,
    difficulty,
    offset,
    limit: PAGE_SIZE,
  });
  const { data: solvedList } = useProgressByProblem(isAuthenticated);
  const solvedIds = new Set(
    (solvedList ?? []).filter((p) => p.first_solved_at).map((p) => p.problem_id)
  );

  const total = data?.total ?? 0;
  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="min-h-full space-y-6 bg-[#0B0F17] p-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Problems</h1>
        <p className="mt-1 text-sm text-gray-500">
          {total} problems across every difficulty and topic.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative max-w-sm flex-1">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-600"
            size={16}
          />
          <input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setOffset(0);
            }}
            placeholder="Search by title..."
            className="w-full rounded-lg border border-gray-800 bg-gray-900/70 py-2 pl-9 pr-3 text-sm text-white placeholder-gray-600 focus:border-cyan-700 focus:outline-none focus:ring-1 focus:ring-cyan-700"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setDifficulty(undefined);
              setOffset(0);
            }}
            className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
              !difficulty
                ? 'bg-cyan-600 text-white'
                : 'bg-gray-900/70 text-gray-400 hover:bg-gray-800'
            }`}
          >
            All
          </button>
          {DIFFICULTIES.map((d) => (
            <button
              key={d}
              onClick={() => {
                setDifficulty(d);
                setOffset(0);
              }}
              className={`rounded-lg px-3.5 py-2 text-sm font-medium capitalize transition-colors ${
                difficulty === d
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gray-900/70 text-gray-400 hover:bg-gray-800'
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-800 bg-gray-900/60">
        {isLoading ? (
          <div className="flex h-40 items-center justify-center">
            <Spinner />
          </div>
        ) : !data || data.items.length === 0 ? (
          <p className="px-6 py-10 text-center text-sm text-gray-500">
            No problems match your filters.
          </p>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                <th className="w-10 px-5 py-3" />
                <th className="px-3 py-3">Title</th>
                <th className="px-3 py-3">Difficulty</th>
                <th className="px-3 py-3">Tags</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/70">
              {data.items.map((problem) => (
                <tr key={problem.id} className="transition-colors hover:bg-gray-800/40">
                  <td className="px-5 py-3">
                    {solvedIds.has(problem.id) && (
                      <CheckCircle2 size={16} className="text-emerald-500" />
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <Link
                      href={`/problems/${problem.id}`}
                      className="text-sm font-medium text-gray-200 hover:text-cyan-400"
                    >
                      {problem.title}
                    </Link>
                  </td>
                  <td className="px-3 py-3">
                    <DifficultyBadge difficulty={problem.difficulty} />
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      {problem.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-gray-800 px-2 py-0.5 text-[11px] capitalize text-gray-400"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {pageCount > 1 && (
        <div className="flex items-center justify-between text-sm">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={offset === 0}
            className="rounded-lg bg-gray-900/70 px-4 py-2 font-medium text-gray-300 transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-gray-500">
            Page {page} of {pageCount}
          </span>
          <button
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={page >= pageCount}
            className="rounded-lg bg-gray-900/70 px-4 py-2 font-medium text-gray-300 transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default ProblemsListPage;
