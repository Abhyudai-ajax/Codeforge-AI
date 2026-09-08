'use client';

import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import {
  authApi,
  contestsApi,
  executionsApi,
  githubApi,
  healthApi,
  interviewsApi,
  languagesApi,
  leaderboardApi,
  notificationsApi,
  problemsApi,
  roadmapsApi,
  roomsApi,
  submissionsApi,
  usersApi,
} from './endpoints';
import type { ExecutionCreate, InterviewType, SubmissionResponse } from './types';

// -------------------------------------------------------------------- health

export function useBackendHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => healthApi.check(),
    refetchInterval: 30_000,
    retry: false,
    staleTime: 0,
  });
}

// ---------------------------------------------------------------------- auth

export function useCurrentUser(enabled: boolean) {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => authApi.me(),
    enabled,
    staleTime: 60_000,
  });
}

// ------------------------------------------------------------------ problems

export function useProblems(params: {
  difficulty?: string;
  language?: string;
  tags?: string;
  search?: string;
  offset?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['problems', params],
    queryFn: () => problemsApi.list(params),
    placeholderData: keepPreviousData,
  });
}

/** The full catalog, cached long — used to resolve problem_id -> title/slug across pages. */
export function useProblemCatalog() {
  return useQuery({
    queryKey: ['problems', 'catalog'],
    queryFn: () => problemsApi.list({ limit: 100 }),
    staleTime: 5 * 60_000,
  });
}

export function useProblem(problemId: string | undefined) {
  return useQuery({
    queryKey: ['problem', problemId],
    queryFn: () => problemsApi.get(problemId as string),
    enabled: !!problemId,
  });
}

export function useRunCode(problemId: string) {
  return useMutation({
    mutationFn: (payload: { language: string; source_code: string }) =>
      problemsApi.run(problemId, payload),
  });
}

export function useSubmitSolution(problemId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { language: string; source_code: string }) =>
      problemsApi.submit(problemId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      queryClient.invalidateQueries({ queryKey: ['progress'] });
      queryClient.invalidateQueries({ queryKey: ['leaderboard'] });
    },
  });
}

export function useProblemHint(problemId: string) {
  return useMutation({
    mutationFn: (payload: { code?: string; language?: string }) =>
      problemsApi.aiHint(problemId, payload),
  });
}

export function useProblemExplain(problemId: string) {
  return useMutation({
    mutationFn: (payload: { code?: string; language?: string }) =>
      problemsApi.aiExplain(problemId, payload),
  });
}

export function useProblemReview(problemId: string) {
  return useMutation({
    mutationFn: (payload: { code?: string; language?: string }) =>
      problemsApi.aiReview(problemId, payload),
  });
}

// --------------------------------------------------------------- submissions

/** Polls a queued/running submission until the judge marks it complete. */
export function useSubmissionPolling(submissionId: string | undefined) {
  return useQuery({
    queryKey: ['submission', submissionId],
    queryFn: () => submissionsApi.get(submissionId as string),
    enabled: !!submissionId,
    refetchInterval: (query) => {
      const data = query.state.data as SubmissionResponse | undefined;
      return data && !data.completed_at ? 1200 : false;
    },
  });
}

export function useProblemSubmissionHistory(problemId: string) {
  return useQuery({
    queryKey: ['submissions', 'by-problem', problemId],
    queryFn: () => problemsApi.submissions(problemId),
    enabled: !!problemId,
  });
}

export function useMySubmissions(limit = 10) {
  return useQuery({
    queryKey: ['submissions', 'mine', limit],
    queryFn: () => usersApi.submissions({ limit }),
  });
}

export function useProgressSummary(enabled: boolean) {
  return useQuery({
    queryKey: ['progress', 'summary'],
    queryFn: () => usersApi.progress(),
    enabled,
  });
}

export function useProgressByProblem(enabled: boolean) {
  return useQuery({
    queryKey: ['progress', 'by-problem'],
    queryFn: () => usersApi.progressByProblem(),
    enabled,
  });
}

// ----------------------------------------------------------------- execution

export function useRunExecution() {
  return useMutation({
    mutationFn: (payload: ExecutionCreate) => executionsApi.create(payload),
  });
}

// ------------------------------------------------------------------ language

export function useLanguages() {
  return useQuery({
    queryKey: ['languages'],
    queryFn: () => languagesApi.list(),
    staleTime: 10 * 60_000,
  });
}

// -------------------------------------------------------------------- roadmap

export function useMyRoadmap(enabled: boolean) {
  return useQuery({
    queryKey: ['roadmap', 'mine'],
    queryFn: () => roadmapsApi.mine(),
    enabled,
  });
}

export function useRoadmaps() {
  return useQuery({
    queryKey: ['roadmap', 'list'],
    queryFn: () => roadmapsApi.list(),
  });
}

export function useRoadmapProgress(enabled: boolean) {
  return useQuery({
    queryKey: ['roadmap', 'progress'],
    queryFn: () => roadmapsApi.progress(),
    enabled,
    retry: false,
  });
}

export function useRoadmapRecommendations(enabled: boolean) {
  return useQuery({
    queryKey: ['roadmap', 'recommendations'],
    queryFn: () => roadmapsApi.recommendations(),
    enabled,
    retry: false,
  });
}

export function useSelectRoadmap() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (roadmapId: string) => roadmapsApi.select(roadmapId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmap'] });
    },
  });
}

// ---------------------------------------------------------------- leaderboard

export function useLeaderboard(params?: { offset?: number; limit?: number }) {
  return useQuery({
    queryKey: ['leaderboard', 'page', params],
    queryFn: () => leaderboardApi.page(params),
    placeholderData: keepPreviousData,
  });
}

export function useMyLeaderboardStanding(enabled: boolean) {
  return useQuery({
    queryKey: ['leaderboard', 'mine'],
    queryFn: () => leaderboardApi.mine(),
    enabled,
  });
}

// ---------------------------------------------------------------- contests

export function useContests(params?: { status?: string; offset?: number; limit?: number }) {
  return useQuery({
    queryKey: ['contests', 'list', params],
    queryFn: () => contestsApi.list(params),
  });
}

export function useContest(contestId: string | undefined) {
  return useQuery({
    queryKey: ['contests', 'detail', contestId],
    queryFn: () => contestsApi.get(contestId as string),
    enabled: !!contestId,
  });
}

export function useContestLeaderboard(
  contestId: string | undefined,
  params?: { offset?: number; limit?: number }
) {
  return useQuery({
    queryKey: ['contests', 'leaderboard', contestId, params],
    queryFn: () => contestsApi.leaderboard(contestId as string, params),
    enabled: !!contestId,
  });
}

export function useMyContestHistory(enabled: boolean) {
  return useQuery({
    queryKey: ['contests', 'my-history'],
    queryFn: () => contestsApi.myHistory(),
    enabled,
  });
}

export function useRegisterContest(contestId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => contestsApi.register(contestId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contests'] }),
  });
}

export function useUnregisterContest(contestId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => contestsApi.unregister(contestId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contests'] }),
  });
}

export function useSubmitContestSolution(contestId: string) {
  return useMutation({
    mutationFn: (payload: { problem_id: string; language: string; source_code: string }) =>
      contestsApi.submit(contestId, payload),
  });
}

// --------------------------------------------------------------- interviews

export function useMyInterviewSessions() {
  return useQuery({
    queryKey: ['interviews', 'mine'],
    queryFn: () => interviewsApi.listMine(),
  });
}

export function useInterviewSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['interviews', 'session', sessionId],
    queryFn: () => interviewsApi.get(sessionId as string),
    enabled: !!sessionId,
  });
}

export function useStartInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { type?: InterviewType; title?: string; time_limit_minutes?: number }) =>
      interviewsApi.start(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['interviews', 'mine'] }),
  });
}

export function useSubmitInterviewAnswer(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { question_id: string; answer_text: string }) =>
      interviewsApi.submitAnswer(sessionId, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['interviews', 'session', sessionId] }),
  });
}

export function useSubmitInterviewCode(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { question_id: string; submission_id: string }) =>
      interviewsApi.submitCode(sessionId, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['interviews', 'session', sessionId] }),
  });
}

export function useFinishInterview(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => interviewsApi.finish(sessionId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['interviews', 'session', sessionId] }),
  });
}

// -------------------------------------------------------------- coding rooms

export function useRooms(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['rooms', 'list', params],
    queryFn: () => roomsApi.list(params),
  });
}

export function useRoom(roomId: string | undefined) {
  return useQuery({
    queryKey: ['rooms', 'detail', roomId],
    queryFn: () => roomsApi.get(roomId as string),
    enabled: !!roomId,
  });
}

export function useCreateRoom() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { title: string; description?: string; is_public?: boolean }) =>
      roomsApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rooms', 'list'] }),
  });
}

export function useJoinRoom() {
  return useMutation({
    mutationFn: (roomId: string) => roomsApi.join(roomId),
  });
}

export function useLeaveRoom() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (roomId: string) => roomsApi.leave(roomId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rooms', 'list'] }),
  });
}

// ------------------------------------------------------------------- github

export function useGithubRepos() {
  return useQuery({
    queryKey: ['github', 'repos'],
    queryFn: () => githubApi.repos(),
  });
}

export function useGithubPullRequest(prId: string | undefined) {
  return useQuery({
    queryKey: ['github', 'pr', prId],
    queryFn: () => githubApi.pullRequest(prId as string),
    enabled: !!prId,
  });
}

export function useGithubAIReview(prId: string) {
  return useMutation({
    mutationFn: () => githubApi.aiReview(prId),
  });
}

// ------------------------------------------------------------- notifications

export function useUnreadNotificationCount(enabled: boolean) {
  return useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => notificationsApi.unreadCount(),
    enabled,
    refetchInterval: 60_000,
  });
}

export function useNotifications(enabled: boolean) {
  return useQuery({
    queryKey: ['notifications', 'list'],
    queryFn: () => notificationsApi.list(),
    enabled,
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

// ----------------------------------------------------------------- utilities

/** Debounces a fast-changing value (search inputs) before it drives a query. */
export function useDebouncedValue<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timeout = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timeout);
  }, [value, delayMs]);
  return debounced;
}

/** Fires `callback` when the user presses Cmd/Ctrl+K, for the topbar search shortcut. */
export function useCommandK(callback: () => void) {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        callbackRef.current();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);
}
