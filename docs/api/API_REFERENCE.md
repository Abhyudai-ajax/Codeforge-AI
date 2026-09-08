# API Reference

CodeForge AI exposes a versioned REST API built with FastAPI. Everything below is
implemented and covered by the backend test suite.

When the backend is running, the always-current contract is served from the app
itself:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

(The interactive docs are only mounted in development mode.)

---

## Authentication

Register or log in to obtain a JWT, then send it on every protected request:

```http
Authorization: Bearer <access_token>
```

Access tokens are short-lived; rotate them with `POST /api/v1/auth/refresh`.
Endpoints marked **admin** additionally require the `admin` role.

---

## Conventions

### Status codes

| Code | Meaning |
| --- | --- |
| `200 OK` | Successful request |
| `201 Created` | Resource created |
| `202 Accepted` | Work queued for a background worker (executions, submissions) |
| `204 No Content` | Successful, empty body |
| `401 Unauthorized` | Missing or invalid token |
| `403 Forbidden` | Authenticated but not permitted |
| `404 Not Found` | Resource missing or inactive |
| `409 Conflict` | Illegal state transition (e.g. cancelling a running job) |
| `422 Unprocessable Entity` | Validation failure, including unsupported languages |
| `503 Service Unavailable` | Job queue unreachable |

### Pagination

List endpoints accept `offset` (`>= 0`) and `limit` (`1..100`) and return:

```json
{ "items": [], "total": 50, "offset": 0, "limit": 20 }
```

---

## Health

| Method | Path |
| --- | --- |
| `GET` | `/api/health` |
| `GET` | `/api/v1/health` |

---

## Languages

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/languages` | Languages the editor can highlight and the sandbox can run |

Drives the editor's language switcher. Response entries:

```json
[
  {
    "id": "c",
    "label": "C (GCC, C17)",
    "monaco_id": "c",
    "file_extension": ".c",
    "compiled": true,
    "is_default": false,
    "starter_code": "#include <stdio.h>\n..."
  }
]
```

Supported ids: `python`, `c`, `cpp`, `javascript`, `java`. Common aliases are
normalized on input, so a client may send `C++`, `js`, `NodeJS` or `python3` and
the API resolves them to the canonical id.

---

## Authentication

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Create an account |
| `POST` | `/api/v1/auth/login` | Exchange credentials for JWTs |
| `POST` | `/api/v1/auth/refresh` | Rotate a refresh token |
| `GET` | `/api/v1/auth/me` | Current authenticated user |
| `GET` | `/api/v1/auth/github/login` | Begin GitHub OAuth |
| `GET` | `/api/v1/auth/github/callback` | GitHub OAuth callback |

## Users

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/users/me` | Profile |
| `PATCH` | `/api/v1/users/me` | Update profile |
| `PUT` | `/api/v1/users/me/password` | Change password |

## Admin

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/admin/users` | List users (**admin**) |
| `PATCH` | `/api/v1/admin/users/{user_id}/role` | Change role or active flag (**admin**) |

---

## DSA Problems

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/problems` | List and filter the catalog |
| `GET` | `/api/v1/problems/search` | Alias of the list route |
| `GET` | `/api/v1/problems/{problem_id}` | Full statement, constraints and starter code |
| `POST` | `/api/v1/problems` | Create (**admin**) |
| `PATCH` | `/api/v1/problems/{problem_id}` | Update (**admin**) |
| `DELETE` | `/api/v1/problems/{problem_id}` | Delete (**admin**) |
| `GET` | `/api/v1/problems/{problem_id}/test-cases` | Includes hidden cases (**admin**) |
| `POST` | `/api/v1/problems/{problem_id}/run` | Run against sample or custom cases |

**List filters** — `difficulty` (`easy`/`medium`/`hard`), `language` (e.g. `c`,
`cpp`), `tags`, `search`, plus `offset` and `limit`.

Public problem responses never include hidden test cases; only the admin
`/test-cases` route exposes them.

### Running code against a problem

`POST /api/v1/problems/{problem_id}/run` executes synchronously against the
problem's public samples, or against `custom_test_cases` when supplied:

```json
{
  "language": "cpp",
  "source_code": "#include <iostream>\nint main(){...}",
  "custom_test_cases": [{ "input": "3\n1 2 3\n", "expected_output": "6\n" }]
}
```

Returns per-case results:

```json
{
  "status": "accepted",
  "passed_test_cases": 2,
  "total_test_cases": 2,
  "runtime_ms": 431,
  "test_results": [
    {
      "test_case": 1,
      "input_data": "3\n1 2 3\n",
      "expected_output": "6\n",
      "actual_output": "6\n",
      "passed": true,
      "runtime_ms": 210,
      "error": ""
    }
  ]
}
```

---

## Submissions & Progress

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/submissions` | Queue a graded submission → `202` |
| `POST` | `/api/v1/problems/{problem_id}/submit` | Same, problem-scoped |
| `GET` | `/api/v1/submissions/{submission_id}` | Poll status and verdict |
| `GET` | `/api/v1/submissions/{submission_id}/result` | Verdict detail |
| `GET` | `/api/v1/problems/{problem_id}/submissions` | Submissions for one problem |
| `GET` | `/api/v1/users/me/submissions` | Submission history |
| `GET` | `/api/v1/users/me/progress` | Aggregate progress |
| `GET` | `/api/v1/users/me/progress/problems` | Per-problem progress |
| `GET` | `/api/v1/users/me/stats` | Summary statistics |

Submissions are graded asynchronously: the API persists the row as `queued` and
returns `202`, then the Celery judge runs every stored test case in an isolated
container and writes the verdict. Poll the submission until `completed_at` is set.

**Statuses** — `queued`, `running`, `accepted`, `wrong_answer`,
`compilation_error`, `runtime_error`, `time_limit_exceeded`,
`memory_limit_exceeded`, `failed`.

Compiler and interpreter output is deliberately **not** echoed verbatim to
clients; the judge returns a short, safe message instead.

---

## Isolated Code Execution

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/executions` | Queue a free-form run → `202` |
| `GET` | `/api/v1/executions/{execution_id}` | Job status |
| `GET` | `/api/v1/executions/{execution_id}/result` | stdout, stderr, exit code, timings |
| `POST` | `/api/v1/executions/{execution_id}/cancel` | Only while `queued`, else `409` |

Unsupported languages are rejected with `422`. See
[EXECUTION_ENGINE.md](../backend/EXECUTION_ENGINE.md) for the sandbox model.

---

## AI Assistance

Generic helpers that operate on any text or code:

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/ai/explain` | Explain code |
| `POST` | `/api/v1/ai/review` | Review code |
| `POST` | `/api/v1/ai/debug` | Debugging guidance |
| `POST` | `/api/v1/ai/tests` | Generate unit tests |
| `POST` | `/api/v1/ai/documentation` | Generate documentation |
| `POST` | `/api/v1/ai/dsa-hint` | Algorithmic hint |

Request/response shape:

```json
{ "content": "def solve(): ...", "additional_context": "optional" }
```
```json
{ "result": "### Code Review Summary ..." }
```

### Problem-scoped AI

These build the prompt from the stored problem statement, tags and constraints,
so the answer is grounded in the actual task rather than pasted text:

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/problems/{problem_id}/ai/hint` | Hint; works with an empty editor |
| `POST` | `/api/v1/problems/{problem_id}/ai/explain` | Explain an approach |
| `POST` | `/api/v1/problems/{problem_id}/ai/review` | Review a solution (`422` if empty) |

```json
{ "code": "#include <stdio.h>\nint main(void){...}", "language": "c" }
```

All AI routes require authentication. When no provider is configured or the
provider call fails, the service returns a structured fallback response rather
than an error, so the editor's AI panel degrades gracefully.

---

## Coding Rooms

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/rooms/` | Create a room |
| `GET` | `/api/v1/rooms/` | List rooms |
| `GET` | `/api/v1/rooms/{room_id}` | Room detail |
| `PATCH` | `/api/v1/rooms/{room_id}` | Update a room |
| `POST` | `/api/v1/rooms/{room_id}/join` | Join |
| `POST` | `/api/v1/rooms/{room_id}/members` | Add a member |
| `DELETE` | `/api/v1/rooms/{room_id}/members/me` | Leave |

Real-time collaboration is served over WebSocket; see
[ARCHITECTURE.md](../architecture/ARCHITECTURE.md).

## Contests & Leaderboards

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/contests` | List contests |
| `POST` | `/api/v1/contests` | Create (**admin**) |
| `GET` | `/api/v1/contests/{contest_id}` | Contest detail |
| `PATCH` | `/api/v1/contests/{contest_id}` | Update (**admin**) |
| `DELETE` | `/api/v1/contests/{contest_id}` | Delete (**admin**) |
| `POST` | `/api/v1/contests/{contest_id}/register` | Register |
| `POST` | `/api/v1/contests/{contest_id}/unregister` | Withdraw |
| `POST` | `/api/v1/contests/{contest_id}/submissions` | Contest submission |
| `GET` | `/api/v1/contests/{contest_id}/leaderboard` | Standings |
| `GET` | `/api/v1/contests/my-history` | Personal contest history |

## Projects

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/projects/` | Create |
| `GET` | `/api/v1/projects/` | My projects |
| `GET` | `/api/v1/projects/public` | Public projects |
| `GET` | `/api/v1/projects/search` | Search public projects |
| `GET` | `/api/v1/projects/{project_id}` | Detail |
| `PATCH` | `/api/v1/projects/{project_id}` | Update |
| `DELETE` | `/api/v1/projects/{project_id}` | Soft delete |
| `POST` | `/api/v1/projects/{project_id}/restore` | Restore |
| `GET` | `/api/v1/projects/{project_id}/files` | File tree |
| `POST` | `/api/v1/projects/{project_id}/files` | Create file or folder |
| `PUT` | `/api/v1/projects/{project_id}/files/{file_id}` | Update file |
| `DELETE` | `/api/v1/projects/{project_id}/files/{file_id}` | Delete file |
| `POST` | `/api/v1/projects/{project_id}/run` | Execute a project file |

## Roadmaps

| Method | Path |
| --- | --- |
| `GET` | `/api/v1/roadmaps/` |
| `GET` | `/api/v1/roadmaps/{identifier}` |
| `GET` | `/api/v1/roadmaps/me` |
| `GET` | `/api/v1/roadmaps/categories` |
| `GET` | `/api/v1/roadmaps/progress` |
| `GET` | `/api/v1/roadmaps/recommendations` |
| `POST` | `/api/v1/roadmaps/select/{roadmap_id}` |
| `POST` | `/api/v1/roadmaps/refresh` |

## Interviews

| Method | Path |
| --- | --- |
| `POST` | `/api/v1/interviews/sessions` |
| `GET` | `/api/v1/interviews/sessions/me` |
| `GET` | `/api/v1/interviews/sessions/{session_id}` |
| `POST` | `/api/v1/interviews/sessions/{session_id}/answer` |
| `POST` | `/api/v1/interviews/sessions/{session_id}/submit-code` |
| `POST` | `/api/v1/interviews/sessions/{session_id}/finish` |
| `GET` | `/api/v1/interviews/sessions/{session_id}/feedback` |

## Notifications

| Method | Path |
| --- | --- |
| `GET` | `/api/v1/notifications/` |
| `GET` | `/api/v1/notifications/unread-count` |
| `PATCH` | `/api/v1/notifications/{notification_id}/read` |
| `POST` | `/api/v1/notifications/read-all` |
| `DELETE` | `/api/v1/notifications/{notification_id}` |

## GitHub Integration

| Method | Path |
| --- | --- |
| `GET` | `/api/v1/github/repos` |
| `GET` | `/api/v1/github/pulls/{pr_id}` |
| `POST` | `/api/v1/github/pulls/{pr_id}/ai-review` |

---

## Error handling

Errors use FastAPI's standard envelope:

```json
{ "detail": "Language is not supported by this problem." }
```

Validation failures (`422`) additionally include a `detail` array identifying the
offending fields.
