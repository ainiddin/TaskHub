# AGENTS.md — TaskHub (TaskFlow)

Instructions for AI coding agents (and humans) working in this repository.
Facts below were checked against the repository at baseline commit `5954516` (tag `baseline-a05`).

## 1. Purpose

TaskFlow is a full-stack task manager: personal tasks, shared workspaces, subtasks, recurring
tasks, activity feed and per-user statistics. It is a student project (KBTU), not a production system.

## 2. Architecture

```
back/    Django 6 + Django REST Framework + SimpleJWT, SQLite
  config/settings.py   settings (dev-only values, see "Known issues")
  api/models.py        Workspace, WorkspaceMember, Task, SubTask, TaskActivity, UserStats
  api/serializers.py   DRF serializers
  api/views.py         all endpoints (function views for auth, generic class views for the rest)
  api/urls.py          routes under /api/
front/   Angular 21 (standalone components), Vitest for unit tests
  src/app/services/    HttpClient services (API base URL is hard-coded to http://127.0.0.1:8000/api)
  src/app/pages/       login, signup, dashboard, tasks, workspace, search, statistics, home
  src/app/interceptors JWT header + refresh on 401;  guards/auth.guard.ts route guard
```

Data flow: Angular -> `/api/...` (JWT Bearer) -> DRF view -> serializer -> model -> SQLite.

## 3. Setup

```bash
# backend (Linux/macOS)                 # Windows PowerShell: .\venv\Scripts\Activate.ps1
cd back
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt         # file is UTF-16 encoded; pip reads it fine
python manage.py migrate
python manage.py runserver              # http://127.0.0.1:8000/

# frontend
cd front
npm ci
npm start                               # http://localhost:4200/
```

Python 3.12+ (Django 6) and Node 20.19+/22.12+ (Angular 21) are required.

## 4. Commands

### Safe — run without asking
| Purpose | Command (from repo root) |
|---|---|
| Backend sanity | `cd back && python manage.py check` |
| Backend tests | `cd back && python manage.py test` |
| Migration drift | `cd back && python manage.py makemigrations --check --dry-run` |
| Frontend build | `cd front && npm run build` |
| Frontend tests | `cd front && npm test -- --watch=false` |
| Read-only git | `git status`, `git diff`, `git log` |

### Ask a human first
- Installing, upgrading or removing any dependency (`pip install`, `npm install <pkg>`, `npm audit fix`).
- Creating or editing migrations (`makemigrations` without `--check`), changing models.
- Editing `back/config/settings.py`, authentication or permission logic.
- Renaming or removing an API route (the frontend hard-codes them).

### Forbidden — never do these
- Reading, printing, creating or committing secrets: `.env`, tokens, the real `SECRET_KEY`.
- Committing `back/db.sqlite3`, `__pycache__/`, `node_modules/`, `dist/` (they are in `.gitignore`).
- Production deployments or any command that talks to a remote server other than package registries.
- Destructive commands: `rm -rf`, `git reset --hard`, `git push --force`, `git clean -fd`,
  `python manage.py flush`, dropping tables, deleting migrations.
- Changing dependencies or lock files without human review.
- Making a failing check pass by deleting/skipping tests, loosening permissions or disabling auth.

## 5. Coding conventions (observed in the code)

- DRF endpoints declare `permission_classes` explicitly (`IsAuthenticated`) and scope querysets to
  `request.user` (personal tasks: `created_by=user, workspace__isnull=True`; workspace tasks:
  `workspace__memberships__user=user`). New endpoints must follow the same rule.
- Any id sent by the client that points to another object (`workspace`, `task`) must be checked
  against the requesting user's access before saving.
- Business rules that do not need HTTP (e.g. recurrence dates) live in plain functions, not in views.
- Frontend: standalone components, services own HTTP calls, Prettier (`printWidth` 100, single quotes),
  `.editorconfig` (2 spaces, final newline).
- Keep changes small: one concern per commit, no drive-by reformatting.

## 6. Test expectations

- Every change to `views.py`, `serializers.py` or `models.py` ships with a backend test in
  `back/api/tests.py` or `back/api/test_*.py`.
- `python manage.py test` printing `Ran 0 tests` / `NO TESTS RAN` is **not** a pass.
- Frontend suite is currently red at baseline (7 of 15 specs fail: missing `ActivatedRoute` provider).
  Do not report it green and do not delete specs to hide it.
- Report real command output (command, pass/fail counts). Never invent results.

## 7. Acceptance criteria (must stay true after any change)

- **AC1 Visibility** — a user sees only their own personal tasks and tasks of workspaces they belong to;
  another user's personal task/subtask returns 404.
- **AC2 Completion rule** — a task with unfinished subtasks cannot be set to `done` (HTTP 400);
  after all subtasks are done it can, and `completed_by`/`completed_at` are set.
- **AC3 Recurrence** — completing a recurring task sets `next_occurrence`: daily +1 day, weekly +7 days,
  monthly +30 days, custom +`repeat_every_days`; non-recurring tasks keep it empty.
- **AC4 Registration & login** — registering creates the user plus a personal workspace where the user is
  `owner` (HTTP 201); login returns `access` and `refresh` tokens.
- **AC5 Workspace roles** — only owner/admin can add members; only the creator can delete a workspace.

## 8. Review gates

1. A human reviews every diff before it is committed; agents do not merge or push to `main`.
2. Each PR/commit description lists the commands run and their real results.
3. If a required command cannot run (network, missing tool), stop and report instead of guessing.
4. Risky areas (auth, permissions, settings, migrations) always need explicit human approval.

## 9. Known issues at baseline (do not "fix" silently — see docs/assignment-05)

Hard-coded dev `SECRET_KEY`, `DEBUG=True`, `ALLOWED_HOSTS=['*']`; committed `db.sqlite3` and `.pyc` files;
no backend tests at baseline; 7 failing frontend specs; 6 production-dependency vulnerabilities reported
by `npm audit --omit=dev`.
