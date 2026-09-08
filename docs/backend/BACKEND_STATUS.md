# Backend Completion Status

_Last verified: 2026-09-06 — `322 passed, 1 skipped`, `flake8` clean._

## Implemented

### Platform
- Auth: register, login, refresh, `me`, and GitHub OAuth login/callback
- User profiles and password change; admin user listing and role management
- Projects: CRUD, soft delete/restore, public listing, search, file tree CRUD,
  and per-file execution
- Coding rooms with membership management and WebSocket collaboration
- Contests with registration, submissions and leaderboards
- Roadmaps, interview sessions and notifications
- GitHub repo/PR integration with AI-assisted PR review

### DSA platform
- 50-problem curated catalog in `app/db/problem_catalog.py`, spanning easy /
  medium / hard across 19 topics (arrays, strings, hashing, two pointers,
  sliding window, stack, queue, linked list, binary search, trees, graphs,
  heaps, DP, greedy, backtracking, sorting, design, bit manipulation, prefix sum)
- Every problem ships a statement, explicit input/output contract, constraints,
  worked examples, an editorial, 4 test cases (2 public samples, 2 hidden), and
  starter code for all five languages
- Idempotent seeder: inserts on a fresh database, refreshes in place on re-run
- Problem listing with difficulty, language, tag and text filters
- Synchronous "run" against samples or custom cases, plus asynchronous graded
  submissions with per-user progress tracking

### Languages and execution
- **Python, C, C++, JavaScript, Java**, defined once in
  `app/core/languages.py` and consumed by every subsystem
- `GET /api/v1/languages` exposes ids, labels, Monaco modes and starter
  scaffolds so the editor can build its language switcher from the backend
- Alias normalization (`C++` → `cpp`, `js` → `javascript`, …)
- Hardened Docker sandbox — see [EXECUTION_ENGINE.md](EXECUTION_ENGINE.md)

### AI
- Generic helpers: explain, review, debug, generate tests, generate
  documentation, DSA hint
- Problem-scoped hint / explain / review that build the prompt from the stored
  statement, tags and constraints
- Provider abstraction (OpenAI, Ollama) with structured fallbacks, so the AI
  panel degrades gracefully when no provider is configured

## Bugs found and fixed during completion

- **The judge task was never registered with the worker.** `app/workers/__init__`
  exported only the execution Celery app, so `codeforge.judge_submission` had no
  consumer — every DSA submission would have sat `queued` forever. Both tasks now
  share one app (`app/workers/celery_app.py`), pinned by
  `tests/test_worker_registration.py`.
- **The seeder crashed.** It popped a non-existent `acceptance_rate` key,
  raising `KeyError` before a single problem was written.
- **`?language=` filtering never matched.** `.contains()` on a generic `JSON`
  column is a string operator, not JSON containment. Replaced with a portable
  serialized-array match that also prevents `c` matching `cpp` and `java`
  matching `javascript`.
- **A seeded test case was unsatisfiable.** `jump-game` expected `true` for
  `[2,0,0,1]`, where index 3 is genuinely unreachable — a correct solution would
  have been marked wrong.

## Verification

- `tests/test_problem_catalog.py` executes each problem's reference solution
  against each of its test cases, so every seeded expected output is proven
  correct rather than assumed (200 case executions).
- `tests/test_sandbox_invocation.py` asserts the exact `docker run` argv,
  including the containment flags, for all five languages.
- `tests/test_runner_images.py` fails if the language registry, the runner
  Dockerfiles and `docker-compose.yml` ever drift apart.
- `tests/test_judge_c_cpp.py` drives accepted / wrong-answer / compilation-error
  paths for C and C++ end to end with the container stubbed.

## CI closes the gaps this machine can't

Neither Docker nor PostgreSQL is installed on the machine this work was done on,
so two things could only be validated statically here and are instead exercised
automatically by `.github/workflows/ci.yml` on every push/PR:

- **`sandbox-smoke-test` job** — builds all five runner images with
  `docker compose --profile runners build` on GitHub's Docker-equipped runner,
  then runs `scripts/docker_smoke_test.py`, which calls the real
  `app.workers.sandbox.run_source` (the exact function the Celery judge calls)
  for every language against a real container: a correct "sum two numbers"
  program must compile and produce the right output, and a deliberately broken
  C/C++ program must fail to compile. No `subprocess.run` stubbing.
- **`backend-test` job, two new steps** — `alembic upgrade head` and
  `python -m app.db.seed_data` now run for real against the job's PostgreSQL
  service, before pytest runs. Previously this Postgres service was started but
  never actually touched: `tests/conftest.py` always points the app at an
  in-memory SQLite database, so nothing had exercised the migration chain or
  the seeder against Postgres-specific behavior (enums, UUID columns, JSON
  columns, batch `ALTER TABLE`).

These will report their first real result on the next push to this branch —
they have not run yet as of this commit.

## Also fixed while wiring up CI

- **`mypy` was failing before this pass**, on files unrelated to the DSA/C++
  work (`alembic/env.py`, `tests/test_coding_rooms.py`), which would have
  blocked `backend-lint` and therefore every downstream CI job. Fixed:
  `config.get_section()` can return `None` per its type stub; and a duck-typed
  test double needed an explicit `cast` to satisfy `WebSocket` typing. Neither
  changes runtime behavior. `mypy .` is now clean (139 files).

## Explicitly deferred

- **Peak memory per submission stays `null`.** Getting a real number requires
  either polling `docker stats` on a running container (races with short jobs
  and adds complexity to the timeout/kill path) or wrapping the sandboxed
  command in a memory-profiling tool and piping its output out through a second
  volume mount — a change to the same code path that isolates untrusted code.
  Without a real Docker daemon available to test against, shipping that change
  unverified was judged worse than leaving the field `null`. Worth revisiting
  once `sandbox-smoke-test` is green and a Docker host is available to
  iterate against directly.
- **Frontend integration** — out of scope per this pass's instructions.

## Remaining work

- Watch the next CI run: confirm `sandbox-smoke-test` and the new
  `backend-test` migration/seed steps are actually green, not just well-formed
  YAML.
- Real secrets (`SECRET_KEY`, OAuth credentials, AI provider keys) still need
  to be filled in per environment; `.env.example` only documents the shape.
