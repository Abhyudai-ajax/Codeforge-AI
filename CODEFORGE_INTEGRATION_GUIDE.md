# Integration Guide

## Structure

- `frontend/components/codeforge`: UI components and page views.
- `frontend/lib/codeforge/types.ts`: shared domain types.
- `frontend/lib/codeforge/apiService.ts`: REST client.
- `frontend/lib/codeforge/useHooks.ts`: React Query hooks.
- `frontend/lib/codeforge/useStore.ts`: persisted Zustand state.
- `frontend/lib/codeforge/utils.ts`: formatting and helper functions.

## API contract

The client expects `/users/me`, `/problems`, `/submissions`, `/submissions/run`, `/leaderboard/global`, `/sessions`, and `/ai/ask` endpoints. Adjust `apiService.ts` if your FastAPI route names differ.

## Authentication

Call `apiService.setAuthToken(token)` after login. Requests automatically attach the token in the browser.

## Extending

Use the existing components as the presentation layer and replace demo data in dashboard/results/leaderboard views with the supplied React Query hooks when the corresponding backend endpoints are available.
