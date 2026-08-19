export type Difficulty = 'EASY' | 'MEDIUM' | 'HARD';
export type SubmissionStatus = 'ACCEPTED' | 'REJECTED' | 'RUNTIME_ERROR' | 'TIME_LIMIT_EXCEEDED' | 'WRONG_ANSWER';

export interface User { id:string; name:string; username:string; email?:string; avatar?:string; rank:number; solved:number; points:number; acceptance:number; rating:number; badge?:string; region?:string; language?:string; }
export interface Example { input:string; output:string; explanation?:string; }
export interface Problem { id:string; number:number; title:string; description:string; difficulty:Difficulty; acceptance:number; solved:number; category:string; tags:string[]; constraints?:string; examples?:Example[]; solved_by_user?:boolean; }
export interface TestCaseResult { id:number; input:string; expected_output:string; actual_output:string; status:'PASSED'|'FAILED'; runtime_ms:number; }
export interface Submission { id:string; problem_id:string; user_id:string; code:string; language:string; status:SubmissionStatus; runtime_ms:number; memory_mb:number; submitted_at:string; test_cases:TestCaseResult[]; }
export interface ActiveSession { id:string; problem_id:string; users:User[]; created_at:string; is_live:boolean; }
export interface LeaderboardEntry { rank:number; user:User; solved:number; points:number; acceptance:number; rating:number; badge?:string; }
export interface CodeEditorState { code:string; language:string; problem_id:string; is_running:boolean; output:string; errors?:string; }
