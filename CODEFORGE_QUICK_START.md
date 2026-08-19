# CodeForge AI Component Library

The component library is integrated under `frontend/components/codeforge` and supporting code under `frontend/lib/codeforge`.

## Run

```bash
cd frontend
npm install
npm run dev
```

Open `/codeforge` for the dashboard, `/codeforge/leaderboard` for rankings, and `/codeforge/submissions` for submission results.

## Backend

Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local`. The API client defaults to `http://localhost:8000/api`.

The existing frontend already includes Axios, Zustand, TanStack Query, Lucide and Tailwind dependencies, so no new package install is required for this integration.
