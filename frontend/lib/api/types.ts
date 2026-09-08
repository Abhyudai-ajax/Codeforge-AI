// TypeScript contracts mirroring the FastAPI backend's Pydantic schemas.
// Keep field names identical to the backend response — no client-side renaming —
// so a schema diff in the API is easy to spot here too.

export type Difficulty = 'easy' | 'medium' | 'hard';

export type SubmissionStatus =
  | 'queued'
  | 'running'
  | 'accepted'
  | 'wrong_answer'
  | 'compilation_error'
  | 'runtime_error'
  | 'time_limit_exceeded'
  | 'memory_limit_exceeded'
  | 'failed';

export type ExecutionStatus =
  | 'queued'
  | 'running'
  | 'completed'
  | 'runtime_error'
  | 'compilation_error'
  | 'timeout'
  | 'failed'
  | 'cancelled';

// ---------------------------------------------------------------- auth/users

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  github_username: string | null;
  created_at: string;
  updated_at: string;
}

// ------------------------------------------------------------------ problems

export interface Page<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface ProblemListItem {
  id: string;
  slug: string;
  title: string;
  difficulty: Difficulty;
  tags: string[];
}

export interface ProblemExample {
  input: string;
  output: string;
}

export interface ProblemResponse extends ProblemListItem {
  description_md: string;
  input_description: string;
  output_description: string;
  constraints: string[];
  examples: ProblemExample[];
  starter_code: Record<string, string>;
  supported_languages: string[];
  time_limit_ms: number;
  memory_limit_mb: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RunTestResult {
  test_case: number;
  input_data: string;
  expected_output: string;
  actual_output: string;
  passed: boolean;
  runtime_ms: number;
  error: string;
}

export interface RunCodeResponse {
  status: string;
  passed_test_cases: number;
  total_test_cases: number;
  runtime_ms: number;
  test_results: RunTestResult[];
}

// --------------------------------------------------------------- submissions

export interface SubmissionResponse {
  id: string;
  user_id: string;
  problem_id: string;
  room_id: string | null;
  language: string;
  status: SubmissionStatus;
  runtime_ms: number | null;
  memory_kb: number | null;
  passed_test_count: number;
  total_test_count: number;
  score: number;
  output: string;
  error_output: string;
  created_at: string;
  completed_at: string | null;
}

export interface ProgressProblemEntry {
  problem_id: string;
  slug: string;
  attempts: number;
  accepted_submissions: number;
  failed_submissions: number;
  first_solved_at: string | null;
}

export interface ProgressSummary {
  attempted: number;
  solved: number;
  by_difficulty: Record<Difficulty, number>;
  total_attempts: number;
}

// ----------------------------------------------------------------- execution

export interface ExecutionCreate {
  language: string;
  source_code: string;
  stdin?: string;
  project_id?: string | null;
  room_id?: string | null;
}

export interface ExecutionResultResponse {
  id: string;
  user_id: string;
  project_id: string | null;
  room_id: string | null;
  language: string;
  status: ExecutionStatus;
  created_at: string;
  completed_at: string | null;
  stdout: string;
  stderr: string;
  exit_code: number | null;
  execution_time_ms: number | null;
  memory_kb: number | null;
}

// ------------------------------------------------------------------ language

export interface LanguageResponse {
  id: string;
  label: string;
  monaco_id: string;
  file_extension: string;
  compiled: boolean;
  is_default: boolean;
  starter_code: string;
}

// -------------------------------------------------------------------- roadmap

export interface CategoryProgress {
  category: string;
  total_problems: number;
  solved_problems: number;
  completion_percentage: number;
}

export interface DifficultyProgress {
  difficulty: Difficulty;
  total_problems: number;
  solved_problems: number;
  completion_percentage: number;
}

export interface RoadmapStageProblemResponse {
  id: string;
  stage_id: string;
  problem_id: string;
  problem_title: string | null;
  problem_slug: string | null;
  problem_difficulty: string | null;
  is_solved: boolean;
  order: number;
  is_required: boolean;
}

export interface RoadmapStageResponse {
  id: string;
  roadmap_id: string;
  title: string;
  slug: string;
  category_name: string;
  description_md: string;
  order: number;
  total_problems: number;
  solved_problems: number;
  problems: RoadmapStageProblemResponse[];
}

export interface RoadmapResponse {
  id: string;
  slug: string;
  title: string;
  description_md: string;
  is_published: boolean;
  is_default: boolean;
  order: number;
  created_at: string;
  updated_at: string;
  stages: RoadmapStageResponse[];
}

export interface UserRoadmapProgressOverview {
  active_roadmap: RoadmapResponse | null;
  total_roadmap_problems: number;
  solved_roadmap_problems: number;
  overall_completion_percentage: number;
  categories: CategoryProgress[];
  difficulties: DifficultyProgress[];
  weak_categories: string[];
}

export interface ProblemRecommendation {
  problem_id: string;
  title: string;
  slug: string;
  category: string;
  difficulty: string;
  reason: string;
}

// ---------------------------------------------------------------- leaderboard

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  solved_count: number;
  points: number;
}

export interface LeaderboardPage {
  items: LeaderboardEntry[];
  total: number;
  offset: number;
  limit: number;
}

export interface MyLeaderboardStanding {
  rank: number | null;
  solved_count: number;
  points: number;
}

// ----------------------------------------------------------------------- AI

export interface AITextResponse {
  result: string;
}

// ------------------------------------------------------------- notifications

export interface NotificationResponse {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  data: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface UnreadCountResponse {
  unread_count: number;
}

// ---------------------------------------------------------------- contests

export type ContestStatus = 'upcoming' | 'running' | 'ended';

export interface ContestListItem {
  id: string;
  title: string;
  slug: string;
  start_time: string;
  end_time: string;
  is_published: boolean;
  status: ContestStatus;
  participant_count: number;
  is_registered: boolean;
  created_at: string;
}

export interface ContestProblemResponse {
  id: string;
  contest_id: string;
  problem_id: string;
  order: number;
  points: number;
  label: string;
  problem: ProblemResponse | null;
}

export interface ContestDetailResponse extends ContestListItem {
  description_md: string;
  problems: ContestProblemResponse[];
}

export interface ContestLeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  full_name: string | null;
  total_score: number;
  total_penalty: number;
  problems_solved: number;
}

export interface ContestLeaderboardPage {
  items: ContestLeaderboardEntry[];
  total: number;
  offset: number;
  limit: number;
}

export interface UserContestHistoryItem {
  contest_id: string;
  title: string;
  slug: string;
  start_time: string;
  end_time: string;
  registered_at: string;
  rank: number | null;
  total_score: number;
  total_penalty: number;
  problems_solved: number;
}

// --------------------------------------------------------------- interviews

export type InterviewType = 'dsa' | 'system_design' | 'behavioral';
export type InterviewStatus = 'in_progress' | 'completed' | 'abandoned';

export interface InterviewQuestionResponse {
  id: string;
  session_id: string;
  problem_id: string | null;
  question_text: string;
  question_type: string;
  order: number;
  points: number;
  problem_title: string | null;
}

export interface InterviewAnswerResponse {
  id: string;
  question_id: string;
  session_id: string;
  user_id: string;
  answer_text: string;
  submission_id: string | null;
  score: number;
  feedback_text: string;
  submitted_at: string;
}

export interface InterviewFeedbackResponse {
  id: string;
  session_id: string;
  overall_score: number;
  strengths: string[];
  improvements: string[];
  summary_md: string;
  evaluated_at: string;
}

export interface InterviewSessionResponse {
  id: string;
  user_id: string;
  type: InterviewType;
  title: string;
  status: InterviewStatus;
  score: number | null;
  time_limit_minutes: number;
  start_time: string | null;
  end_time: string | null;
  created_at: string;
  questions: InterviewQuestionResponse[];
  answers: InterviewAnswerResponse[];
  feedback: InterviewFeedbackResponse | null;
}

// -------------------------------------------------------------- coding rooms

export type RoomMemberRole = 'owner' | 'editor' | 'viewer';

export interface RoomDocument {
  code: string;
  language: string;
}

export interface CodingRoomResponse {
  id: string;
  owner_id: string;
  title: string;
  description: string | null;
  is_public: boolean;
  document: RoomDocument;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface CodingRoomListResponse {
  items: CodingRoomResponse[];
  total: number;
  skip: number;
  limit: number;
}

export interface RoomMemberResponse {
  user_id: string;
  role: RoomMemberRole;
  joined_at: string;
  last_seen_at: string;
}

// ------------------------------------------------------------------- github

export interface GithubRepository {
  id: string;
  name: string;
  owner: string;
  default_branch: string;
  branches: string[];
  is_private: boolean;
  stars: number;
  forks: number;
}

export interface GithubFileDiff {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  patch: string;
}

export interface GithubPullRequest {
  id: string;
  title: string;
  number: number;
  author: string;
  source_branch: string;
  target_branch: string;
  status: string;
  created_at: string;
  files: GithubFileDiff[];
}

export interface GithubAIReview {
  summary: string;
  code_quality_score: number;
  security_risk: string;
  suggestions: { file: string; line: number; type: string; comment: string }[];
}
