'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  Play,
  Send,
  Flame,
  Route as RouteIcon,
  Trophy,
  Sparkles,
  ChevronRight,
  Clock,
} from 'lucide-react';
import { DifficultyBadge, StatCard, RankBadge, Spinner, EmptyState } from './SharedComponents';
import CodeEditor from './CodeEditor';
import { RunResultsPanel, SubmissionStatusPanel } from './RunResultsPanel';
import AIPanel from './AIPanel';
import { useAuthStore } from '@/store/auth';
import { apiErrorMessage } from '@/lib/api/client';
import {
  useProblemCatalog,
  useProblem,
  useRunCode,
  useSubmitSolution,
  useSubmissionPolling,
  useMySubmissions,
  useProgressSummary,
  useProgressByProblem,
  useMyRoadmap,
  useRoadmapProgress,
  useLeaderboard,
  useMyLeaderboardStanding,
} from '@/lib/api/hooks';
import {
  pickDailyProblem,
  msUntilMidnight,
  formatCountdown,
  computeStreak,
  statusColor,
  formatStatusLabel,
} from '@/lib/api/derived';
import type { ProblemListItem, RunCodeResponse } from '@/lib/api/types';

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const { data: catalog } = useProblemCatalog();
  const dailyMeta = useMemo(
    () => (catalog ? pickDailyProblem<ProblemListItem>(catalog.items) : null),
    [catalog]
  );
  const { data: daily } = useProblem(dailyMeta?.id);

  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [runResult, setRunResult] = useState<RunCodeResponse | null>(null);
  const [submissionId, setSubmissionId] = useState<string | undefined>();
  const [countdown, setCountdown] = useState(() => formatCountdown(msUntilMidnight()));

  useEffect(() => {
    const timer = setInterval(() => setCountdown(formatCountdown(msUntilMidnight())), 30_000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!daily) return;
    const initialLanguage = daily.supported_languages.includes('python')
      ? 'python'
      : daily.supported_languages[0];
    setLanguage(initialLanguage);
    setCode(daily.starter_code[initialLanguage] ?? '');
    setRunResult(null);
    setSubmissionId(undefined);
  }, [daily?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleLanguageChange = (nextLanguage: string) => {
    setLanguage(nextLanguage);
    if (daily) setCode(daily.starter_code[nextLanguage] ?? '');
    setRunResult(null);
  };

  const runMutation = useRunCode(daily?.id ?? '');
  const submitMutation = useSubmitSolution(daily?.id ?? '');
  const { data: polledSubmission } = useSubmissionPolling(submissionId);

  const { data: recentSubmissions } = useMySubmissions(50);
  const { data: progress } = useProgressSummary(true);
  const { data: progressByProblem } = useProgressByProblem(true);
  const { data: roadmap } = useMyRoadmap(true);
  const { data: roadmapProgress } = useRoadmapProgress(!!roadmap);
  const { data: topLeaders } = useLeaderboard({ limit: 3 });
  const { data: myStanding } = useMyLeaderboardStanding(true);

  const streak = useMemo(() => computeStreak(recentSubmissions ?? []), [recentSubmissions]);

  const accuracy = useMemo(() => {
    if (!progressByProblem || progressByProblem.length === 0) return null;
    const accepted = progressByProblem.reduce((sum, p) => sum + p.accepted_submissions, 0);
    const total = progressByProblem.reduce(
      (sum, p) => sum + p.accepted_submissions + p.failed_submissions,
      0
    );
    return total > 0 ? Math.round((accepted / total) * 100) : null;
  }, [progressByProblem]);

  const difficultyTotals = useMemo(() => {
    const items = catalog?.items ?? [];
    const count = (d: string) => items.filter((p) => p.difficulty === d).length;
    return { easy: count('easy'), medium: count('medium'), hard: count('hard') };
  }, [catalog]);

  const problemsById = useMemo(() => {
    const map = new Map<string, ProblemListItem>();
    catalog?.items.forEach((p) => map.set(p.id, p));
    return map;
  }, [catalog]);

  const [actionError, setActionError] = useState<string | null>(null);

  const handleRun = () => {
    setRunResult(null);
    setActionError(null);
    runMutation.mutate(
      { language, source_code: code },
      {
        onSuccess: (data) => setRunResult(data),
        onError: (err) =>
          setActionError(apiErrorMessage(err, 'Could not run your code. Try again in a moment.')),
      }
    );
  };

  const handleSubmit = () => {
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
  };

  const notableSubmission = recentSubmissions?.find(
    (s) => s.completed_at && s.status !== 'accepted'
  );

  return (
    <div className="min-h-full space-y-6 bg-[#0B0F17] p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {greeting()}, {user?.full_name?.split(' ')[0] || user?.username || 'there'}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Keep your momentum. Your daily challenge is ready.
          </p>
        </div>
        <div className="flex items-center gap-3 rounded-lg border border-amber-800/50 bg-amber-950/30 px-4 py-2.5">
          <Flame size={20} className="text-amber-400" />
          <div>
            <p className="text-sm font-bold text-amber-300">{streak.current} DAY STREAK</p>
            <p className="text-xs text-amber-600">Personal best: {streak.best} days</p>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-6 xl:flex-row">
        {/* Left column */}
        <div className="flex flex-1 flex-col gap-6">
          <div className="rounded-lg border border-gray-800 bg-gray-900/60">
            <div className="flex flex-wrap items-center gap-3 border-b border-gray-800 px-5 py-3">
              <span className="rounded-md bg-cyan-900/40 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-cyan-400">
                Daily challenge
              </span>
              {daily && <DifficultyBadge difficulty={daily.difficulty} />}
              <span className="ml-auto flex items-center gap-1.5 text-xs text-gray-500">
                <Clock size={13} />
                {countdown}
              </span>
            </div>

            {!daily ? (
              <div className="flex h-40 items-center justify-center">
                <Spinner />
              </div>
            ) : (
              <>
                <div className="border-b border-gray-800 p-5">
                  <div className="mb-3 flex items-center justify-between">
                    <Link
                      href={`/problems/${daily.id}`}
                      className="text-lg font-bold text-white hover:text-cyan-400"
                    >
                      {daily.title}
                    </Link>
                    <div className="flex flex-wrap gap-1.5">
                      {daily.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-gray-800 px-2 py-0.5 text-[11px] capitalize text-gray-400"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <p className="line-clamp-2 text-sm leading-relaxed text-gray-400">
                    {daily.description_md}
                  </p>
                </div>

                <div className="flex flex-col gap-4 p-5">
                  <CodeEditor
                    value={code}
                    onChange={setCode}
                    language={language}
                    onLanguageChange={handleLanguageChange}
                    availableLanguages={daily.supported_languages}
                    height="360px"
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
                      onClick={handleRun}
                      disabled={runMutation.isPending}
                      className="flex items-center gap-2 rounded-lg bg-gray-800 px-5 py-2.5 text-sm font-semibold text-gray-200 transition-colors hover:bg-gray-700 disabled:opacity-50"
                    >
                      <Play size={16} />
                      {runMutation.isPending ? 'Running...' : 'Run'}
                    </button>
                    <button
                      onClick={handleSubmit}
                      disabled={submitMutation.isPending}
                      className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-500 disabled:opacity-50"
                    >
                      <Send size={16} />
                      {submitMutation.isPending ? 'Submitting...' : 'Submit'}
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900/60">
            <div className="flex items-center justify-between border-b border-gray-800 px-5 py-3.5">
              <h3 className="text-sm font-semibold text-white">Recent submissions</h3>
              <Link
                href="/submissions"
                className="flex items-center gap-1 text-xs font-medium text-cyan-400 hover:text-cyan-300"
              >
                View all <ChevronRight size={14} />
              </Link>
            </div>
            {!recentSubmissions || recentSubmissions.length === 0 ? (
              <div className="p-5">
                <EmptyState
                  title="No submissions yet"
                  description="Solve the daily challenge to see your history here."
                />
              </div>
            ) : (
              <div className="divide-y divide-gray-800/70">
                {recentSubmissions.slice(0, 5).map((submission) => {
                  const problem = problemsById.get(submission.problem_id);
                  return (
                    <Link
                      key={submission.id}
                      href={`/submissions/${submission.id}`}
                      className="flex items-center justify-between gap-4 px-5 py-3 transition-colors hover:bg-gray-800/40"
                    >
                      <span className="truncate text-sm font-medium text-gray-200">
                        {problem?.title ?? submission.problem_id}
                      </span>
                      <span className="shrink-0 text-xs uppercase text-gray-500">
                        {submission.language}
                      </span>
                      <span className="w-14 shrink-0 text-right text-xs text-gray-500">
                        {submission.runtime_ms != null ? `${submission.runtime_ms}ms` : '—'}
                      </span>
                      <span
                        className={`w-28 shrink-0 text-right text-xs font-semibold ${statusColor(submission.status)}`}
                      >
                        {formatStatusLabel(submission.status)}
                      </span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right column */}
        <div className="flex w-full flex-col gap-6 xl:w-96">
          <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">Your progress</h3>
            </div>
            <div className="mb-4 grid grid-cols-3 gap-3">
              <StatCard label="Solved" value={progress?.solved ?? '—'} color="emerald" />
              <StatCard
                label="Accuracy"
                value={accuracy != null ? `${accuracy}%` : '—'}
                color="cyan"
              />
              <StatCard
                label="Rank"
                value={myStanding?.rank ? `#${myStanding.rank}` : 'Unranked'}
                color="amber"
              />
            </div>
            <div className="space-y-2.5">
              <DifficultyBar
                label="Easy"
                solved={progress?.by_difficulty.easy ?? 0}
                total={difficultyTotals.easy}
                color="bg-emerald-500"
              />
              <DifficultyBar
                label="Medium"
                solved={progress?.by_difficulty.medium ?? 0}
                total={difficultyTotals.medium}
                color="bg-amber-500"
              />
              <DifficultyBar
                label="Hard"
                solved={progress?.by_difficulty.hard ?? 0}
                total={difficultyTotals.hard}
                color="bg-rose-500"
              />
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
                <RouteIcon size={15} className="text-cyan-400" />
                DSA roadmap
              </h3>
              {roadmapProgress && (
                <span className="text-xs font-semibold text-cyan-400">
                  {Math.round(roadmapProgress.overall_completion_percentage)}%
                </span>
              )}
            </div>
            {!roadmap ? (
              <EmptyState
                title="No roadmap selected"
                description="Pick a guided path to structure your practice."
                action={
                  <Link
                    href="/roadmaps"
                    className="text-xs font-semibold text-cyan-400 hover:text-cyan-300"
                  >
                    Browse roadmaps →
                  </Link>
                }
              />
            ) : (
              <>
                <div className="mb-4 space-y-2">
                  {roadmap.stages.slice(0, 3).map((stage) => (
                    <div key={stage.id} className="flex items-center gap-3">
                      <div
                        className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                          stage.solved_problems >= stage.total_problems && stage.total_problems > 0
                            ? 'bg-emerald-600 text-white'
                            : 'border border-cyan-700 text-cyan-400'
                        }`}
                      >
                        {stage.solved_problems >= stage.total_problems && stage.total_problems > 0
                          ? '✓'
                          : ''}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-gray-200">{stage.title}</p>
                        <p className="text-xs text-gray-500">
                          {stage.solved_problems}/{stage.total_problems} completed
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
                <Link
                  href="/roadmaps"
                  className="block w-full rounded-lg bg-gray-800 py-2 text-center text-sm font-medium text-gray-200 transition-colors hover:bg-gray-700"
                >
                  Continue roadmap
                </Link>
              </>
            )}
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
                <Trophy size={15} className="text-amber-400" />
                Weekly leaderboard
              </h3>
              <Link
                href="/leaderboard"
                className="text-xs font-medium text-cyan-400 hover:text-cyan-300"
              >
                View all
              </Link>
            </div>
            {!topLeaders || topLeaders.items.length === 0 ? (
              <EmptyState
                title="No solves yet"
                description="Be the first to appear on the leaderboard."
              />
            ) : (
              <div className="space-y-1">
                {topLeaders.items.map((entry) => (
                  <div
                    key={entry.user_id}
                    className="flex items-center gap-3 rounded-md px-1 py-1.5"
                  >
                    <RankBadge rank={entry.rank} />
                    <span className="flex-1 truncate text-sm text-gray-300">{entry.username}</span>
                    <span className="text-sm font-semibold text-gray-400">
                      {entry.points.toLocaleString()}
                    </span>
                  </div>
                ))}
                {myStanding?.rank && myStanding.rank > 3 && (
                  <div className="mt-2 flex items-center gap-3 rounded-md border border-cyan-800/50 bg-cyan-950/30 px-2 py-1.5">
                    <span className="w-6 text-center font-mono text-sm text-cyan-400">
                      {myStanding.rank}
                    </span>
                    <span className="flex-1 truncate text-sm font-medium text-cyan-300">You</span>
                    <span className="text-sm font-semibold text-cyan-400">
                      {myStanding.points.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          {notableSubmission && (
            <Link
              href={`/submissions/${notableSubmission.id}`}
              className="flex items-center gap-3 rounded-lg border border-cyan-800/50 bg-cyan-950/20 p-4 transition-colors hover:bg-cyan-950/40"
            >
              <Sparkles size={18} className="shrink-0 text-cyan-400" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-white">AI code review is ready</p>
                <p className="text-xs text-gray-500">Get suggestions on your last submission</p>
              </div>
              <ChevronRight size={16} className="text-gray-600" />
            </Link>
          )}

          {daily && <AIPanel problemId={daily.id} code={code} language={language} />}
        </div>
      </div>
    </div>
  );
};

const DifficultyBar: React.FC<{ label: string; solved: number; total: number; color: string }> = ({
  label,
  solved,
  total,
  color,
}) => {
  const percent = total > 0 ? Math.min(100, (solved / total) * 100) : 0;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-gray-500">{label}</span>
        <span className="font-medium text-gray-400">
          {solved} / {total}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-800">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
};

export default DashboardPage;
