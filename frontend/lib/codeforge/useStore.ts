'use client';
import {create} from 'zustand';
import {persist} from 'zustand/middleware';
import type {CodeEditorState,Submission,User,Problem} from './types';
type State={currentUser?:User;currentProblem?:Problem;editor:CodeEditorState;submissions:Submission[];sidebarOpen:boolean;setUser:(u:User)=>void;setProblem:(p:Problem)=>void;setEditor:(p:Partial<CodeEditorState>)=>void;addSubmission:(s:Submission)=>void;toggleSidebar:()=>void};
export const useCodeForgeStore=create<State>()(persist((set)=>({editor:{code:'',language:'Python 3',problem_id:'',is_running:false,output:''},submissions:[],sidebarOpen:true,setUser:(currentUser)=>set({currentUser}),setProblem:(currentProblem)=>set({currentProblem}),setEditor:(p)=>set(s=>({editor:{...s.editor,...p}})),addSubmission:(s)=>set(x=>({submissions:[s,...x.submissions]})),toggleSidebar:()=>set(s=>({sidebarOpen:!s.sidebarOpen}))}),{name:'codeforge-ai'}));
export const useCurrentUser=()=>useCodeForgeStore(s=>s.currentUser);
export const useEditorState=()=>useCodeForgeStore(s=>s.editor);
