'use client';

import React from 'react';
import Link from 'next/link';
import { CheckCircle, AlertCircle, ArrowLeft, Sparkles } from 'lucide-react';
import { StatCard, StatusBadge, Spinner } from './SharedComponents';
import AIPanel from './AIPanel';
import { useSubmissionPolling, useProblem } from '@/lib/api/hooks';

const SubmissionResultsPage: React.FC<{ submissionId: string }> = ({ submissionId }) => {
  const { data: submission, isLoading } = useSubmissionPolling(submissionId);
  const { data: problem } = useProblem(submission?.problem_id);

  if (isLoading || !submission) {
    return (
      <div className="flex h-full items-center justify-center bg-[#0B0F17]">
        <Spinner size={28} />
      </div>
    );
  }

  const isAccepted = submission.status === 'accepted';
  const isPending = !submission.completed_at;

  return (
    <div className="min-h-full bg-[#0B0F17] p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <Link
          href="/submissions"
          className="flex w-fit items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-300"
        >
          <ArrowLeft size={13} /> Back to submissions
        </Link>

        <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-8 text-center">
          <div className="mb-4 flex justify-center">
            {isPending ? (
              <div className="h-14 w-14 animate-spin rounded-full border-4 border-gray-700 border-t-cyan-500" />
            ) : isAccepted ? (
              <CheckCircle size={56} className="text-emerald-400" />
            ) : (
              <AlertCircle size={56} className="text-rose-400" />
            )}
          </div>
          <StatusBadge status={submission.status} />
          {problem && (
            <p className="mt-3 text-sm text-gray-400">
              for{' '}
              <Link href={`/problems/${problem.id}`} className="text-cyan-400 hover:text-cyan-300">
                {problem.title}
              </Link>
            </p>
          )}
          <p className="mt-1 text-xs text-gray-600">
            Submitted {new Date(submission.created_at).toLocaleString()}
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <StatCard
            label="Runtime"
            value={submission.runtime_ms ?? '—'}
            unit={submission.runtime_ms != null ? 'ms' : ''}
            color="emerald"
          />
          <StatCard
            label="Tests passed"
            value={`${submission.passed_test_count}/${submission.total_test_count}`}
            color="cyan"
          />
          <StatCard label="Language" value={submission.language} color="amber" />
        </div>

        {submission.error_output && (
          <div className="rounded-lg border border-rose-900/50 bg-rose-950/20 p-4">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-rose-500">
              Error
            </p>
            <p className="font-mono text-sm text-rose-300">{submission.error_output}</p>
          </div>
        )}

        {problem && !isAccepted && submission.completed_at && (
          <div className="flex items-center gap-2 rounded-lg border border-cyan-800/40 bg-cyan-950/20 px-4 py-3 text-sm text-cyan-300">
            <Sparkles size={15} />
            Ask the AI assistant below to review why this submission didn&apos;t pass.
          </div>
        )}

        {problem && <AIPanel problemId={problem.id} code={''} language={submission.language} />}
      </div>
    </div>
  );
};

export default SubmissionResultsPage;
