import axios from 'axios';
import type { Problem, Submission, User, LeaderboardEntry, ActiveSession } from './types';
const client=axios.create({baseURL:process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api',headers:{'Content-Type':'application/json'}});
if(typeof window!=='undefined') client.interceptors.request.use(c=>{const t=localStorage.getItem('auth_token');if(t)c.headers.Authorization=`Bearer ${t}`;return c});
export const apiService={
 getCurrentUser:async()=> (await client.get<User>('/users/me')).data,
 getProblems:async(params?:Record<string,unknown>)=> (await client.get<Problem[]>('/problems',{params})).data,
 getProblemById:async(id:string)=> (await client.get<Problem>(`/problems/${id}`)).data,
 searchProblems:async(q:string)=> (await client.get<Problem[]>('/problems/search',{params:{q}})).data,
 submitCode:async(problem_id:string,code:string,language:string)=>(await client.post<Submission>('/submissions',{problem_id,code,language})).data,
 runCode:async(problem_id:string,code:string,language:string)=>(await client.post<{output:string;error?:string}>('/submissions/run',{problem_id,code,language})).data,
 getSubmission:async(id:string)=>(await client.get<Submission>(`/submissions/${id}`)).data,
 getUserSubmissions:async(id:string)=>(await client.get<Submission[]>(`/submissions/user/${id}`)).data,
 getGlobalLeaderboard:async(timeframe='Overall',page=1,limit=50)=>(await client.get<LeaderboardEntry[]>('/leaderboard/global',{params:{timeframe,page,limit}})).data,
 createSession:async(problem_id:string)=>(await client.post<ActiveSession>('/sessions',{problem_id})).data,
 joinSession:async(id:string)=>(await client.post<ActiveSession>(`/sessions/${id}/join`)).data,
 askAI:async(question:string)=>(await client.post<{answer:string}>('/ai/ask',{question})).data.answer,
 setAuthToken:(token:string)=>{if(typeof window!=='undefined')localStorage.setItem('auth_token',token)},
 clearAuthToken:()=>{if(typeof window!=='undefined')localStorage.removeItem('auth_token')}
};
export default apiService;
