'use client';

import React, { useMemo } from 'react';
import Link from 'next/link';
import { StatusBadge, Spinner, EmptyState } from './SharedComponents';
import { useMySubmissions, useProblemCatalog } from '@/lib/api/hooks';

const SubmissionsListPage: React.FC = () => {
  const { data: submissions, isLoading } = useMySubmissions(50);
  const { data: catalog } = useProblemCatalog();

  const problemsById = useMemo(() => {
    const map = new Map<string, { title: string; slug: string }>();
    catalog?.items.forEach((p) => map.set(p.id, { title: p.title, slug: p.slug }));
    return map;
  }, [catalog]);

  return (
    <div className="min-h-full space-y-6 bg-[#0B0F17] p-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Submissions</h1>
        <p className="mt-1 text-sm text-gray-500">
          Every solution you&apos;ve submitted, most recent first.
        </p>
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-800 bg-gray-900/60">
        {isLoading ? (
          <div className="flex h-40 items-center justify-center">
            <Spinner />
          </div>
        ) : !submissions || submissions.length === 0 ? (
          <div className="p-6">
            <EmptyState
              title="No submissions yet"
              description="Solve a problem and submit your solution to see it here."
              action={
                <Link
                  href="/problems"
                  className="text-sm font-semibold text-cyan-400 hover:text-cyan-300"
                >
                  Browse problems →
                </Link>
              }
            />
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                <th className="px-5 py-3">Problem</th>
                <th className="px-3 py-3">Language</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Runtime</th>
                <th className="px-3 py-3">Submitted</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/70">
              {submissions.map((submission) => (
                <tr key={submission.id} className="transition-colors hover:bg-gray-800/40">
                  <td className="px-5 py-3">
                    <Link
                      href={`/submissions/${submission.id}`}
                      className="text-sm font-medium text-gray-200 hover:text-cyan-400"
                    >
                      {problemsById.get(submission.problem_id)?.title ?? submission.problem_id}
                    </Link>
                  </td>
                  <td className="px-3 py-3 text-sm uppercase text-gray-500">
                    {submission.language}
                  </td>
                  <td className="px-3 py-3">
                    <StatusBadge status={submission.completed_at ? submission.status : 'queued'} />
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-500">
                    {submission.runtime_ms != null ? `${submission.runtime_ms}ms` : '—'}
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-500">
                    {new Date(submission.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default SubmissionsListPage;
