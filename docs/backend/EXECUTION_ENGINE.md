# Isolated execution engine

The API persists a queued job and Celery dispatches it to a worker. Only that
worker mounts the Docker socket; the FastAPI service never receives it.

## Supported languages

| Id | Toolchain | Source file | Compiled |
| --- | --- | --- | --- |
| `python` | Python 3.12 | `main.py` | no |
| `c` | GCC, `-std=c17` (Alpine) | `main.c` | yes |
| `cpp` | GCC `g++`, `-std=c++17` (Alpine) | `main.cpp` | yes |
| `javascript` | Node 22 | `main.js` | no |
| `java` | Temurin JDK 21 | `Main.java` | yes |

`backend/app/core/languages.py` is the single source of truth. It defines each
language's runner image, source filename, argv, Monaco syntax mode and editor
starter scaffold. The sandbox, the execution service, both Celery workers, the
`/api/v1/languages` endpoint and the problem seeder all read from it, so adding a
language means editing that file plus adding a matching runner image.

Common aliases (`C++`, `js`, `node`, `python3`, …) are normalized to canonical
ids on the way in.

Compiled languages report a non-zero exit as `compilation_error`; interpreted
languages report `runtime_error`. `tests/test_runner_images.py` fails the build
if a registry entry ever lacks a Dockerfile or a compose build target.

## Building and running

On a Linux Docker host:

```sh
# Build the five runner images (required before any job can execute).
docker compose --profile runners build

# Start the stack with the worker enabled.
docker compose --profile workers up -d postgres redis backend celery
```

The worker is started as `celery -A app.workers:app worker`. That entrypoint
registers **both** `codeforge.execute_job` (free-form runs) and
`codeforge.judge_submission` (DSA grading) on one Celery app — they share a
broker and queue, so they must share an app or the worker would silently reject
the other's messages as unregistered.

## Containment

Each job runs in its own throwaway container with:

- `--network none` — no network access at all
- `--read-only` root filesystem, with a bounded `tmpfs` at `/tmp`
  (`noexec,nosuid,size=64m`) for compiler output
- `--cap-drop ALL` and `--security-opt no-new-privileges`
- `--user 10001:10001` — never root; the runner images create this user
- `--memory` from the problem's limit and `--cpus 0.5`
- `--pids-limit 64` to contain fork bombs
- the source mounted read-only at `/workspace`, in a temporary directory that is
  deleted when the run returns
- a wall-clock timeout derived from the problem's time limit

stdout and stderr are truncated to 64 KiB. Compiler diagnostics are not relayed
to clients verbatim — the judge substitutes a short, safe message.

Peak memory is left `null` rather than guessed: the cgroup limit is enforced, but
reporting an actual peak needs a runner-side metric protocol that does not exist
yet.

## Deployment warning

The Docker socket is root-equivalent on the host. Mount it only into the
dedicated execution worker, deploy that worker as a trusted, isolated service,
and never expose it on a network port or mount it into the API container.
