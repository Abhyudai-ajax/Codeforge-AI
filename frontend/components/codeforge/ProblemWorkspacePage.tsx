'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowLeft, Play, Send, History } from 'lucide-react';
import { DifficultyBadge, Spinner, Tabs } from './SharedComponents';
import CodeEditor from './CodeEditor';
import { RunResultsPanel, SubmissionStatusPanel } from './RunResultsPanel';
import AIPanel from './AIPanel';
import {
  useProblem,
  useRunCode,
  useSubmitSolution,
  useSubmissionPolling,
  useProblemSubmissionHistory,
} from '@/lib/api/hooks';
import type { RunCodeResponse } from '@/lib/api/types';
import { formatStatusLabel, statusColor } from '@/lib/api/derived';
import { apiErrorMessage } from '@/lib/api/client';

const ProblemWorkspacePage: React.FC<{ problemId: string }> = ({ problemId }) => {
  const { data: problem, isLoading } = useProblem(problemId);
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [runResult, setRunResult] = useState<RunCodeResponse | null>(null);
  const [submissionId, setSubmissionId] = useState<string | undefined>();
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (!problem) return;
    const initialLanguage = problem.supported_languages.includes('python')
      ? 'python'
      : problem.supported_languages[0];
    setLanguage(initialLanguage);
    setCode(problem.starter_code[initialLanguage] ?? '');
    setRunResult(null);
    setSubmissionId(undefined);
  }, [problem?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleLanguageChange = (nextLanguage: string) => {
    setLanguage(nextLanguage);
    if (problem) setCode(problem.starter_code[nextLanguage] ?? '');
    setRunResult(null);
  };

  const runMutation = useRunCode(problemId);
  const submitMutation = useSubmitSolution(problemId);
  const { data: polledSubmission } = useSubmissionPolling(submissionId);
  const { data: history } = useProblemSubmissionHistory(problemId);

  if (isLoading || !problem) {
    return (
      <div className="flex h-full items-center justify-center bg-[#0B0F17]">
        <Spinner size={28} />
      </div>
    );
  }

  const statementContent = (
    <div className="markdown-body max-w-none text-sm text-gray-300">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{problem.description_md}</ReactMarkdown>
      {problem.constraints.length > 0 && (
        <>
          <h3>Constraints</h3>
          <ul>
            {problem.constraints.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );

  const historyContent = (
    <div className="space-y-2">
      {!history || history.length === 0 ? (
        <p className="text-sm text-gray-500">No previous submissions for this problem.</p>
      ) : (
        history.map((submission) => (
          <Link
            key={submission.id}
            href={`/submissions/${submission.id}`}
            className="flex items-center justify-between rounded-lg border border-gray-800 bg-gray-900/60 px-4 py-3 transition-colors hover:bg-gray-800/60"
          >
            <span className="text-sm uppercase text-gray-400">{submission.language}</span>
            <span className="text-xs text-gray-600">
              {new Date(submission.created_at).toLocaleString()}
            </span>
            <span className={`text-sm font-semibold ${statusColor(submission.status)}`}>
              {formatStatusLabel(submission.status)}
            </span>
          </Link>
        ))
      )}
    </div>
  );

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[#0B0F17] lg:flex-row">
      <div className="flex w-full flex-col overflow-y-auto border-b border-gray-800 p-6 lg:w-[42%] lg:border-b-0 lg:border-r">
        <Link
          href="/problems"
          className="mb-4 flex w-fit items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-300"
        >
          <ArrowLeft size={13} /> Back to problems
        </Link>
        <div className="mb-4 flex items-center gap-3">
          <h1 className="text-xl font-bold text-white">{problem.title}</h1>
          <DifficultyBadge difficulty={problem.difficulty} />
        </div>
        <div className="mb-6 flex flex-wrap gap-1.5">
          {problem.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-gray-800 px-2.5 py-0.5 text-[11px] capitalize text-gray-400"
            >
              {tag}
            </span>
          ))}
        </div>
        <Tabs
          tabs={[
            { label: 'Statement', value: 'statement', content: statementContent },
            {
              label: 'History',
              value: 'history',
              content: (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <History size={14} />
                  {historyContent}
                </div>
              ),
            },
          ]}
        />
      </div>

      <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-6">
        <CodeEditor
          value={code}
          onChange={setCode}
          language={language}
          onLanguageChange={handleLanguageChange}
          availableLanguages={problem.supported_languages}
          height="440px"
        />
        {actionError && (
          <div className="rounded-lg border border-rose-900/50 bg-rose-950/30 px-4 py-2.5 text-sm text-rose-400">
            {actionError}
          </div>
        )}
        {runResult && <RunResultsPanel result={runResult} />}
        {polledSubmission && <SubmissionStatusPanel submission={polledSubmission} />}

        <div className="flex gap-3">
          <button
            onClick={() => {
              setRunResult(null);
              setActionError(null);
              runMutation.mutate(
                { language, source_code: code },
                {
                  onSuccess: setRunResult,
                  onError: (err) =>
                    setActionError(
                      apiErrorMessage(err, 'Could not run your code. Try again in a moment.')
                    ),
                }
              );
            }}
            disabled={runMutation.isPending}
            className="flex items-center gap-2 rounded-lg bg-gray-800 px-5 py-2.5 text-sm font-semibold text-gray-200 transition-colors hover:bg-gray-700 disabled:opacity-50"
          >
            <Play size={16} />
            {runMutation.isPending ? 'Running...' : 'Run'}
          </button>
          <button
            onClick={() => {
              setSubmissionId(undefined);
              setActionError(null);
              submitMutation.mutate(
                { language, source_code: code },
                {
                  onSuccess: (data) => setSubmissionId(data.id),
                  onError: (err) =>
                    setActionError(
                      apiErrorMessage(err, 'Could not submit your solution. Try again in a moment.')
                    ),
                }
              );
            }}
            disabled={submitMutation.isPending}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-500 disabled:opacity-50"
          >
            <Send size={16} />
            {submitMutation.isPending ? 'Submitting...' : 'Submit'}
          </button>
        </div>

        <AIPanel problemId={problemId} code={code} language={language} />
      </div>
    </div>
  );
};

export default ProblemWorkspacePage;
