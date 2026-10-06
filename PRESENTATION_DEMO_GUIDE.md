# 🚀 CodeForge AI — Presentation & Live Demo Guide

This guide contains everything you need for tomorrow's presentation:
1. **How to Launch Everything (1-Click)**
2. **Slide-by-Slide Talking Points (10-Page Presentation)**
3. **Live Demonstration Walkthrough Steps**
4. **Platform Capabilities & Architecture Verification**
5. **Expected Questions & Answers (Viva / Evaluators Q&A)**

---

## ⚡ 1. How to Launch the Project

We have verified and tuned the entire system. Both backend and frontend are tested and verified.

### Quick Start (Double Click or Run Script)
Run either of these from the project root `E:\CodeForge AI`:
- **Double click**: `run_codeforge.bat`
- **Or via PowerShell**: `.\run_codeforge.ps1`

### Or Launch Manually in 2 Terminals:

#### Terminal 1 — Backend (FastAPI):
```powershell
cd "e:\CodeForge AI\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
> **Backend URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)  
> **Interactive Swagger Docs**: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)

#### Terminal 2 — Frontend (Next.js):
```powershell
cd "e:\CodeForge AI\frontend"
npm run dev
```
> **Frontend URL**: [http://localhost:3000](http://localhost:3000)

### Pre-configured Demo Login Credentials:
- **Email**: `demo@codeforge.ai`
- **Password**: `password123`
- *(Already seeded into the database with 50 DSA problems and an active demo workspace!)*

---

## 🖥️ 2. The 10-Slide Interactive Presentation Deck

Your presentation file is located at:
`e:\CodeForge AI\presentation.html`

> Simply double-click `presentation.html` to open it in Chrome, Edge, or Brave.  
> Press **F11** for immersive full-screen mode.  
> Use **Left/Right Arrow Keys**, **Spacebar**, or the bottom navigation buttons to switch slides.

### Slide-by-Slide Walkthrough

| Slide # | Slide Title | Core Message & Talking Points |
| :---: | :--- | :--- |
| **1** | **Title Slide: CodeForge AI** | Introduce the platform: Next-generation AI-powered cloud IDE and competitive programming ecosystem built for modern developers. |
| **2** | **The Problem Space** | Existing coding platforms are fragmented: LeetCode offers static problems without multi-file context; Replit/VS Code lack competitive judging and structured DSA roadmaps; ChatGPT lacks IDE context and test-case awareness. |
| **3** | **The CodeForge AI Solution** | A unified ecosystem combining a cloud IDE (Monaco Editor), an automated multi-language execution judge, an in-editor AI Copilot, and real-time multiplayer collaboration. |
| **4** | **System Architecture** | Modern decoupled architecture: Next.js 14 App Router frontend + FastAPI async backend + SQLAlchemy async ORM + SQLite/PostgreSQL + Celery/Redis workers + Sandboxed code runner. |
| **5** | **How It Compares (Market Advantage)** | Side-by-side comparison matrix with LeetCode, HackerRank, Replit, and GitHub Codespaces. Highlight: AI hint generation (not just code dump), multi-file DSA problems, contest engine. |
| **6** | **Current Working Prototype** | What is built and working right now: 50 DSA problems catalog, authentication with JWT, Monaco code editor, local execution fallback, contest manager, real-time leaderboard, and resilient AI copilot. |
| **7** | **AI Copilot & Intelligence Layer** | Capabilities of the AI layer: Semantic code explanation, bug detection & automated debugging, complexity analysis ($O(N)$ time & space), and pedagogical Socratic hinting. |
| **8** | **Multiplayer & Contest Engine** | Live timed contest platform with penalty calculation, real-time leaderboards, problem submission gating, and contest registration workflow. |
| **9** | **Future Roadmap** | What comes next: Dockerized gVisor microVM sandboxes, WebRTC video/audio peer pair-programming, dynamic AI test-case generation, and custom enterprise coding assessments. |
| **10** | **Conclusion & Q&A** | Summary of engineering achievements (300+ unit/integration tests passing, type-safe Next.js + FastAPI) and inviting questions from the jury/audience. |

---

## 🎬 3. Live Demonstration Script (Step-by-Step)

Follow this sequence during your live demo to impress evaluators:

1. **Step 1: Landing Page & Authenticity**
   - Open [http://localhost:3000](http://localhost:3000).
   - Show the dark-mode developer UI, hero animations, and feature highlights.
2. **Step 2: Authentication & Profile**
   - Click **Login** (or navigate to `/login`).
   - Enter `demo@codeforge.ai` / `password123`.
   - Show that JWT tokens are safely stored and the user session is active.
3. **Step 3: DSA Problem Catalog**
   - Navigate to `/problems`.
   - Point out the 50 DSA problems with tags (`Array`, `Dynamic Programming`, `Graphs`, etc.) and difficulty badges (Easy, Medium, Hard).
   - Select a problem (e.g., Two Sum or Reverse Linked List).
4. **Step 4: Cloud IDE & Code Execution**
   - Open the problem workspace.
   - Show the Monaco Editor with syntax highlighting, language selector (Python, C, C++, Java, JS), and test case panel.
   - Click **Run Code** to show real-time test execution and output.
5. **Step 5: AI Copilot in Action**
   - Trigger the AI assistant (Explain Code, Review, or Hint).
   - Demonstrate how it provides structured, actionable feedback (Time/Space complexity, edge cases) rather than merely spoiling the answer.
6. **Step 6: Contests & Leaderboards**
   - Navigate to `/contests`.
   - Show active sprint contests, problem point values, and the live leaderboard with rank calculation.

---

## 🛡️ 4. Verification & Testing Summary

During our check of all project components:
- **Database**: Initialized with SQLite async engine and seeded with 50 problems, demo user, and demo project.
- **Backend Test Suite**: Passed **300 test cases** across authentication, problems catalog, projects, contests, notifications, and AI schemas.
- **Code Execution**: Configured with a local subprocess fallback so code runs on Windows without requiring Docker daemon.
- **Frontend Code Quality**: Verified with `tsc --noEmit` (**0 errors**) and ESLint (**0 errors**).
- **Backend API Routes**: Verified live with health check, problem querying, and JWT token issuance.

---

## 💡 5. Expected Evaluator Questions & Answers

**Q1: How do you prevent malicious code execution if Docker is not installed?**  
> *"In production, CodeForge AI utilizes isolated Docker containers with drop-privilege non-root execution, CPU and memory limits, and no network access. For local developer environments without Docker, a subprocess runner with strict execution timeouts (e.g., 5 seconds) acts as a graceful fallback."*

**Q2: What makes the AI Copilot different from copying into ChatGPT?**  
> *"CodeForge AI integrates the AI directly into the problem context. The prompts are conditioned on the problem constraints, input/output specifications, and the user's current editor AST. Furthermore, our system is prompt-engineered for Socratic guidance—providing algorithmic hints rather than spoiling solutions."*

**Q3: How is real-time contest scoring calculated?**  
> *"The contest engine scores submissions based on public and hidden test cases, tracking total points and submission penalties based on timestamp and failed attempts, using ranked window functions in SQL for real-time leaderboards."*

Good luck with your presentation tomorrow!
