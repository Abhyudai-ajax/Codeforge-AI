'use client';

import React from 'react';
import { CheckCircle2, Circle, Sparkles } from 'lucide-react';
import { Spinner, EmptyState, Button, DifficultyBadge } from './SharedComponents';
import Link from 'next/link';
import {
  useRoadmaps,
  useMyRoadmap,
  useRoadmapProgress,
  useRoadmapRecommendations,
  useSelectRoadmap,
} from '@/lib/api/hooks';

const RoadmapsPage: React.FC = () => {
  const { data: roadmaps, isLoading: loadingRoadmaps } = useRoadmaps();
  const { data: myRoadmap } = useMyRoadmap(true);
  const { data: progress } = useRoadmapProgress(!!myRoadmap);
  const { data: recommendations } = useRoadmapRecommendations(!!myRoadmap);
  const selectRoadmap = useSelectRoadmap();

  return (
    <div className="min-h-full bg-[#0B0F17] p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">DSA Roadmaps</h1>
          <p className="mt-1 text-sm text-gray-500">
            Structured paths through the problem catalog, by topic.
          </p>
        </div>

        {!myRoadmap ? (
          <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-6">
            <h2 className="mb-4 text-sm font-semibold text-white">
              Choose a roadmap to start tracking progress
            </h2>
            {loadingRoadmaps ? (
              <Spinner />
            ) : !roadmaps || roadmaps.length === 0 ? (
              <EmptyState title="No roadmaps published yet" />
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {roadmaps.map((roadmap) => (
                  <div
                    key={roadmap.id}
                    className="rounded-lg border border-gray-800 bg-gray-950/40 p-4"
                  >
                    <h3 className="font-semibold text-white">{roadmap.title}</h3>
                    <p className="mt-1 line-clamp-2 text-xs text-gray-500">
                      {roadmap.description_md}
                    </p>
                    <p className="mt-2 text-xs text-gray-600">{roadmap.stages.length} stages</p>
                    <Button
                      size="sm"
                      className="mt-3"
                      disabled={selectRoadmap.isPending}
                      onClick={() => selectRoadmap.mutate(roadmap.id)}
                    >
                      Select this roadmap
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-bold text-white">{myRoadmap.title}</h2>
                {progress && (
                  <span className="text-sm font-semibold text-cyan-400">
                    {Math.round(progress.overall_completion_percentage)}% complete
                  </span>
                )}
              </div>
              {progress && (
                <div className="mb-6 h-2 w-full overflow-hidden rounded-full bg-gray-800">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500"
                    style={{ width: `${progress.overall_completion_percentage}%` }}
                  />
                </div>
              )}

              <div className="space-y-3">
                {myRoadmap.stages.map((stage) => (
                  <div
                    key={stage.id}
                    className="rounded-lg border border-gray-800 bg-gray-950/40 p-4"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <h3 className="font-semibold text-white">{stage.title}</h3>
                      <span className="text-xs text-gray-500">
                        {stage.solved_problems}/{stage.total_problems}
                      </span>
                    </div>
                    <div className="space-y-1.5">
                      {stage.problems.map((p) => (
                        <Link
                          key={p.id}
                          href={p.problem_id ? `/problems/${p.problem_id}` : '#'}
                          className="flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-gray-800/60"
                        >
                          {p.is_solved ? (
                            <CheckCircle2 size={15} className="shrink-0 text-emerald-500" />
                          ) : (
                            <Circle size={15} className="shrink-0 text-gray-700" />
                          )}
                          <span
                            className={p.is_solved ? 'text-gray-500 line-through' : 'text-gray-300'}
                          >
                            {p.problem_title}
                          </span>
                          {p.problem_difficulty && (
                            <DifficultyBadge
                              difficulty={p.problem_difficulty}
                              className="ml-auto"
                            />
                          )}
                        </Link>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {progress && progress.weak_categories.length > 0 && (
              <div className="rounded-lg border border-amber-800/40 bg-amber-950/10 p-5">
                <p className="text-sm font-semibold text-amber-300">Focus areas</p>
                <p className="mt-1 text-xs text-amber-600">
                  {progress.weak_categories.join(', ')} — lowest completion among your active
                  categories.
                </p>
              </div>
            )}

            {recommendations && recommendations.length > 0 && (
              <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
                <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
                  <Sparkles size={15} className="text-cyan-400" />
                  Recommended next
                </h3>
                <div className="space-y-2">
                  {recommendations.slice(0, 5).map((rec) => (
                    <Link
                      key={rec.problem_id}
                      href={`/problems/${rec.problem_id}`}
                      className="flex items-center justify-between rounded-md border border-gray-800 bg-gray-950/40 px-3 py-2.5 transition-colors hover:bg-gray-800/60"
                    >
                      <div>
                        <p className="text-sm font-medium text-gray-200">{rec.title}</p>
                        <p className="text-xs text-gray-500">{rec.reason}</p>
                      </div>
                      <DifficultyBadge difficulty={rec.difficulty} />
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default RoadmapsPage;
