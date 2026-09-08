'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Brain, Clock, ChevronRight } from 'lucide-react';
import { Button, Spinner, EmptyState } from './SharedComponents';
import { useMyInterviewSessions, useStartInterview } from '@/lib/api/hooks';
import { apiErrorMessage } from '@/lib/api/client';
import type { InterviewType } from '@/lib/api/types';

const TYPES: { id: InterviewType; label: string; description: string }[] = [
  {
    id: 'dsa',
    label: 'DSA Coding',
    description: 'Two algorithmic problems, solved and judged like a real submission.',
  },
  {
    id: 'system_design',
    label: 'System Design',
    description: 'Open-ended design questions, answered in writing.',
  },
  {
    id: 'behavioral',
    label: 'Behavioral',
    description: 'Situational and teamwork questions, answered in writing.',
  },
];

const InterviewsPage: React.FC = () => {
  const router = useRouter();
  const { data: sessions, isLoading } = useMyInterviewSessions();
  const startMutation = useStartInterview();
  const [error, setError] = useState<string | null>(null);

  const start = (type: InterviewType) => {
    setError(null);
    startMutation.mutate(
      { type },
      {
        onSuccess: (session) => router.push(`/interviews/${session.id}`),
        onError: (err) => setError(apiErrorMessage(err, 'Could not start the interview.')),
      }
    );
  };

  return (
    <div className="min-h-full space-y-6 bg-[#0B0F17] p-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold text-white">
          <Brain size={22} className="text-cyan-400" />
          Mock Interviews
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Timed practice sessions with AI-evaluated feedback at the end.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-900/50 bg-rose-950/30 px-4 py-2.5 text-sm text-rose-400">
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        {TYPES.map((t) => (
          <div
            key={t.id}
            className="flex flex-col rounded-lg border border-gray-800 bg-gray-900/60 p-5"
          >
            <h3 className="font-semibold text-white">{t.label}</h3>
            <p className="mt-1 flex-1 text-xs text-gray-500">{t.description}</p>
            <Button
              size="sm"
              className="mt-4"
              disabled={startMutation.isPending}
              onClick={() => start(t.id)}
            >
              Start session
            </Button>
          </div>
        ))}
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-white">Past sessions</h2>
        {isLoading ? (
          <div className="flex h-32 items-center justify-center">
            <Spinner />
          </div>
        ) : !sessions || sessions.length === 0 ? (
          <EmptyState
            title="No interview sessions yet"
            description="Start one above to begin practicing."
          />
        ) : (
          <div className="space-y-2">
            {sessions.map((session) => (
              <Link
                key={session.id}
                href={`/interviews/${session.id}`}
                className="flex items-center gap-4 rounded-lg border border-gray-800 bg-gray-900/60 px-5 py-3.5 transition-colors hover:bg-gray-800/50"
              >
                <span className="flex-1 text-sm font-medium text-gray-200">{session.title}</span>
                <span className="text-xs uppercase text-gray-500">
                  {session.type.replace('_', ' ')}
                </span>
                <span
                  className={`text-xs font-semibold ${session.status === 'completed' ? 'text-emerald-400' : 'text-amber-400'}`}
                >
                  {session.status.replace('_', ' ')}
                </span>
                {session.score != null && (
                  <span className="text-xs text-gray-400">{session.score.toFixed(0)}%</span>
                )}
                <span className="flex items-center gap-1 text-xs text-gray-600">
                  <Clock size={12} />
                  {session.time_limit_minutes}m
                </span>
                <ChevronRight size={15} className="text-gray-600" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default InterviewsPage;
