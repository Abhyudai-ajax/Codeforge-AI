'use client';

import React, { useState } from 'react';
import { Github, GitPullRequest, Info, Sparkles, Plus, Minus } from 'lucide-react';
import { Spinner, Button } from './SharedComponents';
import { useGithubRepos, useGithubPullRequest, useGithubAIReview } from '@/lib/api/hooks';
import { apiErrorMessage } from '@/lib/api/client';

// The backend's /github endpoints are currently a fixed demo dataset (a
// single hardcoded repo, one seeded PR "pr-101") pending real GitHub OAuth
// wiring — this page calls those real endpoints and shows whatever they
// return, rather than fabricating additional data on top of them.
const DEMO_PR_ID = 'pr-101';

const GitHubReviewPage: React.FC = () => {
  const { data: repos, isLoading: reposLoading } = useGithubRepos();
  const { data: pr, isLoading: prLoading } = useGithubPullRequest(DEMO_PR_ID);
  const reviewMutation = useGithubAIReview(DEMO_PR_ID);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="min-h-full space-y-6 bg-[#0B0F17] p-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold text-white">
          <Github size={22} />
          GitHub review
        </h1>
        <p className="mt-1 text-sm text-gray-500">AI-assisted pull request review.</p>
      </div>

      <div className="flex items-start gap-2 rounded-lg border border-cyan-800/40 bg-cyan-950/20 px-4 py-3 text-xs text-cyan-300">
        <Info size={14} className="mt-0.5 shrink-0" />
        This integration is backed by a fixed demo dataset on the server pending real GitHub OAuth —
        the repo and pull request below are illustrative, not live data from your account.
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-white">Repositories</h2>
        {reposLoading ? (
          <Spinner />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {(repos ?? []).map((repo) => (
              <div key={repo.id} className="rounded-lg border border-gray-800 bg-gray-900/60 p-4">
                <p className="font-medium text-white">
                  {repo.owner}/{repo.name}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {repo.branches.length} branches · default {repo.default_branch}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
          <GitPullRequest size={15} className="text-cyan-400" />
          Pull request
        </h2>
        {prLoading ? (
          <Spinner />
        ) : !pr ? (
          <p className="text-sm text-gray-500">No pull request found.</p>
        ) : (
          <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
            <div className="mb-1 flex items-center justify-between">
              <p className="font-medium text-white">
                #{pr.number} {pr.title}
              </p>
              <span className="rounded-full border border-emerald-700 bg-emerald-900/30 px-2 py-0.5 text-[11px] font-semibold uppercase text-emerald-400">
                {pr.status}
              </span>
            </div>
            <p className="mb-4 text-xs text-gray-500">
              {pr.author} · {pr.source_branch} → {pr.target_branch}
            </p>

            <div className="space-y-3">
              {pr.files.map((file) => (
                <div
                  key={file.filename}
                  className="overflow-hidden rounded-lg border border-gray-800"
                >
                  <div className="flex items-center justify-between bg-gray-800/60 px-3 py-2 text-xs">
                    <span className="font-mono text-gray-300">{file.filename}</span>
                    <span className="flex items-center gap-2 text-gray-500">
                      <span className="flex items-center gap-0.5 text-emerald-400">
                        <Plus size={11} />
                        {file.additions}
                      </span>
                      <span className="flex items-center gap-0.5 text-rose-400">
                        <Minus size={11} />
                        {file.deletions}
                      </span>
                    </span>
                  </div>
                  <pre className="overflow-x-auto bg-gray-950/60 p-3 font-mono text-xs text-gray-400">
                    {file.patch}
                  </pre>
                </div>
              ))}
            </div>

            <Button
              className="mt-4"
              disabled={reviewMutation.isPending}
              onClick={() => {
                setError(null);
                reviewMutation.mutate(undefined, {
                  onError: (err) =>
                    setError(apiErrorMessage(err, 'Could not generate an AI review.')),
                });
              }}
            >
              <Sparkles size={15} />
              {reviewMutation.isPending ? 'Reviewing...' : 'Generate AI review'}
            </Button>
            {error && <p className="mt-2 text-sm text-rose-400">{error}</p>}

            {reviewMutation.data && (
              <div className="mt-4 space-y-3 rounded-lg border border-gray-800 bg-gray-950/40 p-4">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-white">
                    Quality score: {reviewMutation.data.code_quality_score}/100
                  </span>
                  <span className="text-xs text-gray-500">
                    Security risk: {reviewMutation.data.security_risk}
                  </span>
                </div>
                <p className="text-sm text-gray-300">{reviewMutation.data.summary}</p>
                {reviewMutation.data.suggestions.length > 0 && (
                  <ul className="space-y-1.5 text-xs text-gray-400">
                    {reviewMutation.data.suggestions.map((s, i) => (
                      <li key={i}>
                        <span className="font-mono text-gray-500">
                          {s.file}:{s.line}
                        </span>{' '}
                        — {s.comment}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GitHubReviewPage;
