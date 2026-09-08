'use client';

import React from 'react';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import type { RunCodeResponse, SubmissionResponse } from '@/lib/api/types';
import { formatStatusLabel, statusColor } from '@/lib/api/derived';

export const RunResultsPanel: React.FC<{ result: RunCodeResponse }> = ({ result }) => (
  <div className="border-t border-gray-800 bg-gray-900/60 p-4">
    <div className="mb-3 flex items-center justify-between">
      <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
        {result.passed_test_cases}/{result.total_test_cases} test cases passed
      </span>
      <span className={`text-xs font-semibold ${statusColor(result.status)}`}>
        {formatStatusLabel(result.status)}
      </span>
    </div>
    <div className="max-h-48 space-y-2 overflow-y-auto">
      {result.test_results.map((testCase) => (
        <div
          key={testCase.test_case}
          className="rounded-md border border-gray-800 bg-gray-950/60 p-3 text-xs"
        >
          <div className="mb-1.5 flex items-center gap-2">
            {testCase.passed ? (
              <CheckCircle2 size={14} className="text-emerald-400" />
            ) : (
              <XCircle size={14} className="text-rose-400" />
            )}
            <span className="font-medium text-gray-300">Case {testCase.test_case}</span>
            <span className="ml-auto text-gray-600">{testCase.runtime_ms}ms</span>
          </div>
          {!testCase.passed && (
            <div className="space-y-1 font-mono text-[11px]">
              <p className="text-gray-500">
                input: <span className="text-gray-400">{truncate(testCase.input_data)}</span>
              </p>
              <p className="text-gray-500">
                expected:{' '}
                <span className="text-emerald-400">{truncate(testCase.expected_output)}</span>
              </p>
              <p className="text-gray-500">
                got:{' '}
                <span className="text-rose-400">
                  {truncate(testCase.actual_output || testCase.error)}
                </span>
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  </div>
);

export const SubmissionStatusPanel: React.FC<{ submission: SubmissionResponse }> = ({
  submission,
}) => {
  const isDone = !!submission.completed_at;
  return (
    <div className="border-t border-gray-800 bg-gray-900/60 p-4">
      <div className="flex items-center gap-2">
        {!isDone && <Loader2 size={15} className="animate-spin text-cyan-400" />}
        <span className={`text-sm font-semibold ${statusColor(submission.status)}`}>
          {formatStatusLabel(submission.status)}
        </span>
        {isDone && (
          <span className="text-xs text-gray-500">
            {submission.passed_test_count}/{submission.total_test_count} tests ·{' '}
            {submission.runtime_ms ?? '—'}ms
          </span>
        )}
      </div>
      {isDone && submission.error_output && (
        <p className="mt-2 font-mono text-xs text-rose-400">{submission.error_output}</p>
      )}
    </div>
  );
};

function truncate(text: string, max = 80): string {
  const clean = text.replace(/\n/g, ' ⏎ ');
  return clean.length > max ? `${clean.slice(0, max)}…` : clean;
}
