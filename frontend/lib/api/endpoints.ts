import { apiClient, healthClient } from './client';
import type {
  AITextResponse,
  CodingRoomListResponse,
  CodingRoomResponse,
  ContestDetailResponse,
  ContestLeaderboardPage,
  ContestListItem,
  ExecutionCreate,
  ExecutionResultResponse,
  GithubAIReview,
  GithubPullRequest,
  GithubRepository,
  InterviewAnswerResponse,
  InterviewFeedbackResponse,
  InterviewSessionResponse,
  InterviewType,
  LanguageResponse,
  LeaderboardPage,
  MyLeaderboardStanding,
  NotificationResponse,
  Page,
  ProblemListItem,
  ProblemResponse,
  ProgressProblemEntry,
  ProgressSummary,
  ProblemRecommendation,
  RoadmapResponse,
  RoomDocument,
  RoomMemberResponse,
  RunCodeResponse,
  SubmissionResponse,
  TokenResponse,
  UnreadCountResponse,
  UserContestHistoryItem,
  UserResponse,
  UserRoadmapProgressOverview,
} from './types';

// -------------------------------------------------------------------- health

export const healthApi = {
  check: () => healthClient.get('/health').then((r) => r.data),
};

// ---------------------------------------------------------------------- auth

export const authApi = {
  register: (payload: { username: string; email: string; password: string; full_name?: string }) =>
    apiClient.post('/auth/register', payload).then((r) => r.data),

  login: (payload: { email: string; password: string }) =>
    apiClient.post<TokenResponse>('/auth/login', payload).then((r) => r.data),

  me: () => apiClient.get<UserResponse>('/auth/me').then((r) => r.data),
};

// --------------------------------------------------------------------- users

export const usersApi = {
  me: () => apiClient.get<UserResponse>('/users/me').then((r) => r.data),

  progress: () => apiClient.get<ProgressSummary>('/users/me/progress').then((r) => r.data),

  progressByProblem: () =>
    apiClient.get<ProgressProblemEntry[]>('/users/me/progress/problems').then((r) => r.data),

  submissions: (params?: { offset?: number; limit?: number }) =>
    apiClient.get<SubmissionResponse[]>('/users/me/submissions', { params }).then((r) => r.data),

  updateProfile: (payload: { full_name?: string; avatar_url?: string; bio?: string }) =>
    apiClient.patch<UserResponse>('/users/me', payload).then((r) => r.data),

  changePassword: (payload: { current_password: string; new_password: string }) =>
    apiClient.put('/users/me/password', payload).then((r) => r.data),
};

// ------------------------------------------------------------------ problems

export const problemsApi = {
  list: (params?: {
    difficulty?: string;
    language?: string;
    tags?: string;
    search?: string;
    offset?: number;
    limit?: number;
  }) => apiClient.get<Page<ProblemListItem>>('/problems', { params }).then((r) => r.data),

  get: (problemId: string) =>
    apiClient.get<ProblemResponse>(`/problems/${problemId}`).then((r) => r.data),

  run: (
    problemId: string,
    payload: {
      language: string;
      source_code: string;
      custom_test_cases?: { input_data: string; expected_output: string }[];
    }
  ) => apiClient.post<RunCodeResponse>(`/problems/${problemId}/run`, payload).then((r) => r.data),

  submit: (problemId: string, payload: { source_code: string; language: string }) =>
    apiClient
      .post<SubmissionResponse>(`/problems/${problemId}/submit`, payload)
      .then((r) => r.data),

  submissions: (problemId: string) =>
    apiClient.get<SubmissionResponse[]>(`/problems/${problemId}/submissions`).then((r) => r.data),

  aiHint: (problemId: string, payload: { code?: string; language?: string }) =>
    apiClient.post<AITextResponse>(`/problems/${problemId}/ai/hint`, payload).then((r) => r.data),

  aiExplain: (problemId: string, payload: { code?: string; language?: string }) =>
    apiClient
      .post<AITextResponse>(`/problems/${problemId}/ai/explain`, payload)
      .then((r) => r.data),

  aiReview: (problemId: string, payload: { code?: string; language?: string }) =>
    apiClient.post<AITextResponse>(`/problems/${problemId}/ai/review`, payload).then((r) => r.data),
};

// ------------------------------------------------------------- generic AI

export const aiApi = {
  explain: (payload: { content: string; additional_context?: string }) =>
    apiClient.post<AITextResponse>('/ai/explain', payload).then((r) => r.data),

  review: (payload: { content: string; additional_context?: string }) =>
    apiClient.post<AITextResponse>('/ai/review', payload).then((r) => r.data),

  debug: (payload: { content: string; additional_context?: string }) =>
    apiClient.post<AITextResponse>('/ai/debug', payload).then((r) => r.data),

  tests: (payload: { content: string; additional_context?: string }) =>
    apiClient.post<AITextResponse>('/ai/tests', payload).then((r) => r.data),

  documentation: (payload: { content: string; additional_context?: string }) =>
    apiClient.post<AITextResponse>('/ai/documentation', payload).then((r) => r.data),
};

// --------------------------------------------------------------- submissions

export const submissionsApi = {
  get: (submissionId: string) =>
    apiClient.get<SubmissionResponse>(`/submissions/${submissionId}`).then((r) => r.data),
};

// ----------------------------------------------------------------- execution

export const executionsApi = {
  create: (payload: ExecutionCreate) => apiClient.post('/executions', payload).then((r) => r.data),

  result: (executionId: string) =>
    apiClient.get<ExecutionResultResponse>(`/executions/${executionId}/result`).then((r) => r.data),
};

// ------------------------------------------------------------------ language

export const languagesApi = {
  list: () => apiClient.get<LanguageResponse[]>('/languages').then((r) => r.data),
};

// -------------------------------------------------------------------- roadmap

export const roadmapsApi = {
  list: () => apiClient.get<RoadmapResponse[]>('/roadmaps/').then((r) => r.data),

  mine: () =>
    apiClient
      .get<RoadmapResponse>('/roadmaps/me')
      .then((r) => r.data)
      .catch(() => null),

  progress: () =>
    apiClient.get<UserRoadmapProgressOverview>('/roadmaps/progress').then((r) => r.data),

  recommendations: () =>
    apiClient.get<ProblemRecommendation[]>('/roadmaps/recommendations').then((r) => r.data),

  select: (roadmapId: string) =>
    apiClient.post(`/roadmaps/select/${roadmapId}`).then((r) => r.data),
};

// ---------------------------------------------------------------- leaderboard

export const leaderboardApi = {
  page: (params?: { offset?: number; limit?: number }) =>
    apiClient.get<LeaderboardPage>('/leaderboard', { params }).then((r) => r.data),

  mine: () => apiClient.get<MyLeaderboardStanding>('/leaderboard/me').then((r) => r.data),
};

// ------------------------------------------------------------- notifications

export const contestsApi = {
  list: (params?: { status?: string; offset?: number; limit?: number }) =>
    apiClient.get<ContestListItem[]>('/contests', { params }).then((r) => r.data),

  get: (contestId: string) =>
    apiClient.get<ContestDetailResponse>(`/contests/${contestId}`).then((r) => r.data),

  register: (contestId: string) =>
    apiClient.post(`/contests/${contestId}/register`).then((r) => r.data),

  unregister: (contestId: string) =>
    apiClient.post(`/contests/${contestId}/unregister`).then((r) => r.data),

  submit: (
    contestId: string,
    payload: { problem_id: string; language: string; source_code: string }
  ) =>
    apiClient
      .post<SubmissionResponse>(`/contests/${contestId}/submissions`, payload)
      .then((r) => r.data),

  leaderboard: (contestId: string, params?: { offset?: number; limit?: number }) =>
    apiClient
      .get<ContestLeaderboardPage>(`/contests/${contestId}/leaderboard`, { params })
      .then((r) => r.data),

  myHistory: () =>
    apiClient.get<UserContestHistoryItem[]>('/contests/my-history').then((r) => r.data),
};

export const interviewsApi = {
  start: (payload: { type?: InterviewType; title?: string; time_limit_minutes?: number }) =>
    apiClient.post<InterviewSessionResponse>('/interviews/sessions', payload).then((r) => r.data),

  listMine: (params?: { offset?: number; limit?: number }) =>
    apiClient
      .get<InterviewSessionResponse[]>('/interviews/sessions/me', { params })
      .then((r) => r.data),

  get: (sessionId: string) =>
    apiClient
      .get<InterviewSessionResponse>(`/interviews/sessions/${sessionId}`)
      .then((r) => r.data),

  submitAnswer: (sessionId: string, payload: { question_id: string; answer_text: string }) =>
    apiClient
      .post<InterviewAnswerResponse>(`/interviews/sessions/${sessionId}/answer`, payload)
      .then((r) => r.data),

  submitCode: (sessionId: string, payload: { question_id: string; submission_id: string }) =>
    apiClient
      .post<InterviewAnswerResponse>(`/interviews/sessions/${sessionId}/submit-code`, payload)
      .then((r) => r.data),

  finish: (sessionId: string) =>
    apiClient
      .post<InterviewSessionResponse>(`/interviews/sessions/${sessionId}/finish`)
      .then((r) => r.data),

  feedback: (sessionId: string) =>
    apiClient
      .get<InterviewFeedbackResponse>(`/interviews/sessions/${sessionId}/feedback`)
      .then((r) => r.data),
};

export const roomsApi = {
  create: (payload: {
    title: string;
    description?: string;
    is_public?: boolean;
    document?: RoomDocument;
  }) => apiClient.post<CodingRoomResponse>('/rooms/', payload).then((r) => r.data),

  list: (params?: { skip?: number; limit?: number }) =>
    apiClient.get<CodingRoomListResponse>('/rooms/', { params }).then((r) => r.data),

  get: (roomId: string) =>
    apiClient.get<CodingRoomResponse>(`/rooms/${roomId}`).then((r) => r.data),

  join: (roomId: string) =>
    apiClient.post<RoomMemberResponse>(`/rooms/${roomId}/join`).then((r) => r.data),

  leave: (roomId: string) => apiClient.delete(`/rooms/${roomId}/members/me`).then((r) => r.data),
};

export const githubApi = {
  repos: () => apiClient.get<GithubRepository[]>('/github/repos').then((r) => r.data),

  pullRequest: (prId: string) =>
    apiClient.get<GithubPullRequest>(`/github/pulls/${prId}`).then((r) => r.data),

  aiReview: (prId: string) =>
    apiClient.post<GithubAIReview>(`/github/pulls/${prId}/ai-review`).then((r) => r.data),
};

export const notificationsApi = {
  list: () => apiClient.get<NotificationResponse[]>('/notifications/').then((r) => r.data),

  unreadCount: () =>
    apiClient.get<UnreadCountResponse>('/notifications/unread-count').then((r) => r.data),

  markRead: (notificationId: string) =>
    apiClient.patch(`/notifications/${notificationId}/read`).then((r) => r.data),

  markAllRead: () => apiClient.post('/notifications/read-all').then((r) => r.data),
};
