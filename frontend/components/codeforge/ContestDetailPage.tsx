'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowLeft, Send, Play } from 'lucide-react';
import { DifficultyBadge, Spinner, EmptyState, Button, Tabs } from './SharedComponents';
import CodeEditor from './CodeEditor';
import { RunResultsPanel } from './RunResultsPanel';
import {
  useContest,
  useContestLeaderboard,
  useRegisterContest,
  useUnregisterContest,
  useSubmitContestSolution,
  useRunCode,
} from '@/lib/api/hooks';
import { apiErrorMessage } from '@/lib/api/client';
import type { ContestProblemResponse, RunCodeResponse } from '@/lib/api/types';

const ContestDetailPage: React.FC<{ contestId: string }> = ({ contestId }) => {
  const { data: contest, isLoading } = useContest(contestId);
  const { data: leaderboard } = useContestLeaderboard(contestId);
  const registerMutation = useRegisterContest(contestId);
  const unregisterMutation = useUnregisterContest(contestId);
  const [selected, setSelected] = useState<ContestProblemResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (isLoading || !contest) {
    return (
      <div className="flex h-full items-center justify-center bg-[#0B0F17]">
        <Spinner size={28} />
      </div>
    );
  }

  const problemsTab = (
    <div className="space-y-2">
      {contest.problems.length === 0 ? (
        <EmptyState title="No problems attached yet" />
      ) : (
        contest.problems
          .sort((a, b) => a.order - b.order)
          .map((cp) => (
            <button
              key={cp.id}
              onClick={() => {
                setSelected(cp);
                setError(null);
              }}
              className={`flex w-full items-center gap-3 rounded-lg border px-4 py-3 text-left transition-colors ${
                selected?.id === cp.id
                  ? 'border-cyan-700 bg-cyan-950/30'
                  : 'border-gray-800 bg-gray-900/60 hover:bg-gray-800/50'
              }`}
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-gray-800 text-xs font-bold text-gray-300">
                {cp.label}
              </span>
              <span className="flex-1 text-sm font-medium text-gray-200">{cp.problem?.title}</span>
              {cp.problem && <DifficultyBadge difficulty={cp.problem.difficulty} />}
              <span className="text-xs text-gray-500">{cp.points} pts</span>
            </button>
          ))
      )}
    </div>
  );

  const leaderboardTab = (
    <div className="overflow-hidden rounded-lg border border-gray-800 bg-gray-900/60">
      {!leaderboard || leaderboard.items.length === 0 ? (
        <div className="p-6">
          <EmptyState
            title="No submissions yet"
            description="Standings appear once someone scores."
          />
        </div>
      ) : (
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              <th className="px-5 py-3">Rank</th>
              <th className="px-3 py-3">User</th>
              <th className="px-3 py-3 text-center">Solved</th>
              <th className="px-3 py-3 text-right">Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/70">
            {leaderboard.items.map((entry) => (
              <tr key={entry.user_id}>
                <td className="px-5 py-3 font-mono text-sm text-gray-400">#{entry.rank}</td>
                <td className="px-3 py-3 text-sm font-medium text-gray-200">
                  {entry.full_name || entry.username}
                </td>
                <td className="px-3 py-3 text-center text-sm text-gray-400">
                  {entry.problems_solved}
                </td>
                <td className="px-3 py-3 text-right text-sm font-semibold text-gray-300">
                  {entry.total_score}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );

  return (
    <div className="min-h-full bg-[#0B0F17] p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <Link
          href="/contests"
          className="flex w-fit items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-300"
        >
          <ArrowLeft size={13} /> Back to contests
        </Link>

        <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-6">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <h1 className="text-xl font-bold text-white">{contest.title}</h1>
            {contest.is_registered ? (
              <Button
                variant="secondary"
                size="sm"
                disabled={unregisterMutation.isPending}
                onClick={() => unregisterMutation.mutate()}
              >
                Unregister
              </Button>
            ) : (
              <Button
                size="sm"
                disabled={registerMutation.isPending}
                onClick={() => registerMutation.mutate()}
              >
                Register
              </Button>
            )}
          </div>
          <p className="mb-3 text-xs text-gray-500">
            {new Date(contest.start_time).toLocaleString()} →{' '}
            {new Date(contest.end_time).toLocaleString()} · {contest.participant_count} registered
          </p>
          <div className="markdown-body text-sm text-gray-300">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{contest.description_md}</ReactMarkdown>
          </div>
        </div>

        <Tabs
          tabs={[
            { label: 'Problems', value: 'problems', content: problemsTab },
            { label: 'Leaderboard', value: 'leaderboard', content: leaderboardTab },
          ]}
        />

        {selected?.problem && (
          <ContestSolvePanel
            contestId={contestId}
            problem={selected}
            registered={contest.is_registered}
            onSubmitError={setError}
          />
        )}
        {error && (
          <div className="rounded-lg border border-rose-900/50 bg-rose-950/30 px-4 py-2.5 text-sm text-rose-400">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

const ContestSolvePanel: React.FC<{
  contestId: string;
  problem: ContestProblemResponse;
  registered: boolean;
  onSubmitError: (message: string | null) => void;
}> = ({ contestId, problem, registered, onSubmitError }) => {
  const languages = problem.problem?.supported_languages ?? ['python'];
  const [language, setLanguage] = useState(languages.includes('python') ? 'python' : languages[0]);
  const [code, setCode] = useState(problem.problem?.starter_code[language] ?? '');
  const [runResult, setRunResult] = useState<RunCodeResponse | null>(null);
  const [submitted, setSubmitted] = useState<string | null>(null);

  const runMutation = useRunCode(problem.problem_id);
  const submitMutation = useSubmitContestSolution(contestId);

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
      <h3 className="mb-4 text-sm font-semibold text-white">
        {problem.label}. {problem.problem?.title}
      </h3>
      <CodeEditor
        value={code}
        onChange={setCode}
        language={language}
        onLanguageChange={(next) => {
          setLanguage(next);
          setCode(problem.problem?.starter_code[next] ?? '');
        }}
        availableLanguages={languages}
        height="320px"
      />
      {runResult && <RunResultsPanel result={runResult} />}
      {submitted && (
        <div className="mt-4 rounded-lg border border-cyan-800/40 bg-cyan-950/20 px-4 py-2.5 text-sm text-cyan-300">
          {submitted}
        </div>
      )}
      <div className="mt-4 flex gap-3">
        <Button
          variant="secondary"
          disabled={runMutation.isPending}
          onClick={() => {
            setRunResult(null);
            runMutation.mutate({ language, source_code: code }, { onSuccess: setRunResult });
          }}
        >
          <Play size={15} />
          {runMutation.isPending ? 'Running...' : 'Run'}
        </Button>
        <Button
          variant="success"
          disabled={!registered || submitMutation.isPending}
          onClick={() => {
            onSubmitError(null);
            setSubmitted(null);
            submitMutation.mutate(
              { problem_id: problem.problem_id, language, source_code: code },
              {
                onSuccess: () =>
                  setSubmitted('Submitted — check the leaderboard for your updated score.'),
                onError: (err) =>
                  onSubmitError(apiErrorMessage(err, 'Could not submit your solution.')),
              }
            );
          }}
        >
          <Send size={15} />
          {registered
            ? submitMutation.isPending
              ? 'Submitting...'
              : 'Submit'
            : 'Register to submit'}
        </Button>
      </div>
    </div>
  );
};

export default ContestDetailPage;
