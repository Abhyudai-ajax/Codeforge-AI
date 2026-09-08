// Small, honest client-side derivations from real API data — no fabricated
// numbers. Each function documents exactly what it computes and from what.

import type { ProblemListItem, SubmissionResponse } from './types';

/** Deterministic "problem of the day": same pick for everyone, changes at local midnight. */
export function pickDailyProblem<T extends ProblemListItem>(problems: T[]): T | null {
  if (problems.length === 0) return null;
  const today = new Date();
  const dayKey = `${today.getFullYear()}-${today.getMonth()}-${today.getDate()}`;
  let hash = 0;
  for (let i = 0; i < dayKey.length; i += 1) {
    hash = (hash * 31 + dayKey.charCodeAt(i)) >>> 0;
  }
  const sorted = [...problems].sort((a, b) => a.id.localeCompare(b.id));
  return sorted[hash % sorted.length];
}

/** Milliseconds until local midnight, for the daily challenge countdown. */
export function msUntilMidnight(): number {
  const now = new Date();
  const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  return midnight.getTime() - now.getTime();
}

export function formatCountdown(ms: number): string {
  if (ms <= 0) return '0m left';
  const totalMinutes = Math.floor(ms / 60_000);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours > 0) return `${hours}h ${minutes}m left`;
  return `${minutes}m left`;
}

/**
 * Current daily streak: consecutive local days (ending today or yesterday)
 * with at least one accepted submission, computed from the caller's recent
 * submission history. Approximate if the fetched page doesn't cover the whole
 * streak, but never fabricated.
 */
export function computeStreak(submissions: SubmissionResponse[]): {
  current: number;
  best: number;
} {
  const acceptedDays = new Set(
    submissions
      .filter((submission) => submission.status === 'accepted')
      .map((submission) => new Date(submission.created_at).toDateString())
  );
  if (acceptedDays.size === 0) return { current: 0, best: 0 };

  const dayMs = 24 * 60 * 60 * 1000;
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let current = 0;
  const startsToday = acceptedDays.has(today.toDateString());
  const cursor = new Date(today);
  if (!startsToday) cursor.setTime(cursor.getTime() - dayMs);
  while (acceptedDays.has(cursor.toDateString())) {
    current += 1;
    cursor.setTime(cursor.getTime() - dayMs);
  }

  // Best run observed within the fetched window (a lower bound on true best).
  const sortedDayTimes = [...acceptedDays].map((d) => new Date(d).getTime()).sort((a, b) => a - b);
  let best = 1;
  let run = 1;
  for (let i = 1; i < sortedDayTimes.length; i += 1) {
    run = sortedDayTimes[i] - sortedDayTimes[i - 1] === dayMs ? run + 1 : 1;
    best = Math.max(best, run);
  }
  return { current, best: Math.max(best, current) };
}

/** A simple, transparent level derived from difficulty-weighted leaderboard points. */
export function levelFromPoints(points: number): number {
  return Math.floor(points / 400) + 1;
}

export function difficultyColor(difficulty: string): string {
  switch (difficulty) {
    case 'easy':
      return 'text-emerald-400 border-emerald-700 bg-emerald-900/30';
    case 'medium':
      return 'text-amber-400 border-amber-700 bg-amber-900/30';
    case 'hard':
      return 'text-rose-400 border-rose-700 bg-rose-900/30';
    default:
      return 'text-gray-400 border-gray-700 bg-gray-900/30';
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case 'accepted':
    case 'completed':
      return 'text-emerald-400';
    case 'queued':
    case 'running':
      return 'text-amber-400';
    default:
      return 'text-rose-400';
  }
}

export function formatStatusLabel(status: string): string {
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function initialsFor(name: string | null | undefined, fallback: string): string {
  const source = (name || fallback || '').trim();
  if (!source) return '?';
  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}
