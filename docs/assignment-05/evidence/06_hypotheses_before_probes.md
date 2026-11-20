# Hypotheses written BEFORE running any probe (read-only AI review, 2026-11-20)

Source: AI assistant (Claude Sonnet 5.5) read back/api/{models,serializers,views,urls}.py,
back/config/settings.py, README.md, front/src/app/services/*.ts, interceptor, guard.
No files were modified during the review. Each line is a PREDICTION, not a result.

| ID  | Category        | Hypothesis (AI prediction)                                                        | Predicted |
|-----|-----------------|-----------------------------------------------------------------------------------|-----------|
| H1  | security        | Non-member can list members of a foreign workspace (GET /api/workspaces/<id>/members/) | 200 (vulnerable) |
| H2  | security        | Non-member can create a task inside a foreign workspace (POST /api/tasks/ workspace=<id>) | 201 (vulnerable) |
| H3  | security        | Non-member can add a subtask to a foreign task, which then blocks completion      | 201 + 400 on done |
| H4  | correctness     | Registering an existing username raises IntegrityError -> HTTP 500                | 500 |
| H5  | security        | Password "1" is accepted at registration (Django validators not applied)          | 201 |
| H6  | correctness     | /api/statistics/?period=custom&date_from=bad&date_to=bad -> HTTP 500              | 500 |
| H7  | maintainability | Every GET /api/statistics/ writes a new UserStats row                             | +1 row/call |
| H8  | security        | Logout does not revoke the refresh token (no blacklist app installed)             | refresh still 200 |
| H9  | security        | A plain "member" can PATCH (rename) a workspace; only DELETE is restricted        | 200 |
| H10 | security        | An admin can add a member with arbitrary role string, including "owner"           | 201 |
| H11 | security        | PATCH /api/tasks/<id>/ can move a task into a workspace the user is not in        | 200 |
| H12 | correctness     | GET /api/tasks/ by user B resets user A's recurring done task (global UPDATE)     | A's task -> not_done |
| H13 | security        | No throttling on /api/login/ (20 wrong passwords -> all 400, never 429)           | all 400 |
| H14 | correctness     | "monthly" recurrence is exactly +30 days, not a calendar month                    | 30 |
| H15 | security        | User B can read user A's personal task by id                                      | 404 (expected NOT vulnerable) |
| H16 | security        | User B can read user A's subtask by id                                            | 404 (expected NOT vulnerable) |
| H17 | security        | ?search= is SQL-injectable                                                        | safe (expected NOT vulnerable) |
| H18 | security        | JWT access tokens never expire                                                    | default 5 min (expected NOT vulnerable) |
| H19 | security        | /api/activities/ leaks events of workspaces the user is not in                    | empty (expected NOT vulnerable) |
| H20 | security        | Anonymous GET /api/tasks/ allowed because of IsAuthenticatedOrReadOnly default    | 401 (expected NOT vulnerable) |

H15-H20 are NEGATIVE CONTROLS: areas that look fine on code reading. They are probed so the
report does not list only positive findings. If a prediction turns out wrong, it is recorded
as wrong in the results file; predictions are not edited after the probes run.
