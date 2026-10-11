# Plan Mode Supervision Log — Task priority feature

Feature: optional `priority` on tasks (int 1–5, 1 = urgent, 5 = low, default 3), accepted on
`POST /tasks` and `PATCH /tasks/<id>`, returned in every task response, filterable with `GET /tasks?priority=<n>`.

Mapping to this codebase: task-manager has no ORM model, so the "Task model" is the dict records in
`TASKS` (`services/tasks.py`). `GET /tasks` and `PATCH /tasks/<id>` did not exist before this project.

Every session below touched more than one file and was run in Plan Mode (Shift+Tab until "plan mode on").

| Session # | Prompt summary (≤15 words) | Did you amend the plan? | What you changed | Did output match amended plan? |
|---|---|---|---|---|
| 1 | Add validated `priority` (default 3) to `TASKS` and `create_task`, with tests | No | No edits to the plan itself. During planning Claude quoted the CLAUDE.md rule "Do not change the signatures of `create_task`" and asked how to handle it; I chose a trailing `priority: int = 3`. I also kept `routes/api.py` out of scope (services + tests only). The plan already rejected bools (`isinstance(priority, bool)`) and tested 0, 6, -1, "high", 2.5, None, True, so nothing needed adding. Note: the plan also added `"priority": 3` to the `TASKS` seed records, which CLAUDE.md forbids, but Claude didn't flag that conflict the way it flagged the signature one; I accepted it because every record needs a priority. | Yes — diff matched every plan step; only `services/tasks.py` and `tests/test_tasks.py` changed; pytest -q 18 passed; ruff clean |
| 2 | Add `list_tasks` and `GET /tasks?priority=n` filter with tests | [Yes/No] | [ ] | [ ] |
| 3 | Add `update_task` and `PATCH /tasks/<id>` for priority with tests | [Yes/No] | [ ] | [ ] |
| 4 | `POST /tasks` accepts priority; route tests in `tests/test_api.py` | [Yes/No] | [ ] | [ ] |

<!--
DELETE THESE COMMENTS BEFORE SUBMITTING.

Requirements: >=4 rows, >=2 rows with "Yes" amended, >=1 row "Partially"/"No" with what diverged and why,
pytest -q passes with >=2 new tests covering priority filtering.

Good "What you changed" cell (full credit):
  "Plan used request.args.get('priority', type=int); I amended it to pass the raw string to the service,
   because type=int silently turns ?priority=abc into None and returns every task instead of a 422."
Bad cell: "Amended the plan."

=============== EXACT PROMPTS (paste at the > cursor, in Plan Mode) ===============

SESSION 1
Add an optional priority field to tasks in @services/tasks.py: an integer 1-5 (1 = urgent, 5 = low), default 3. Every task record in TASKS must include "priority", and create_task must accept priority and reject invalid values with ValidationError. Add tests in @tests/test_tasks.py. Run pytest -q when done.

  Amend if the plan...
  - edits the seed records in TASKS -> CLAUDE.md forbids changing seed data. Decide: allow ONLY adding
    "priority": 3 to each seed record (ids, titles, done, user_id unchanged). Say so explicitly.
  - changes create_task(title, user_id) in a breaking way -> CLAUDE.md forbids signature changes.
    Amend: "add priority: int = 3 as the LAST parameter so routes/api.py and existing tests still work".
  - validates with isinstance(priority, int) only -> isinstance(True, int) is True in Python.
    Amend: "reject bool too, and reject strings like '3'".
  - only tests one bad value -> amend: "test 0, 6, True and '3' all raise ValidationError".

SESSION 2
Add list_tasks to @services/tasks.py that returns all tasks, optionally filtered by priority, and a GET /tasks route in @routes/api.py that supports ?priority=<n>. An invalid priority must return 422 through ValidationError. Add at least two tests for priority filtering. Run pytest -q when done.

  Amend if the plan...
  - uses request.args.get("priority", type=int) -> Flask returns None for "abc", so ?priority=abc
    silently returns ALL tasks. Amend: "route passes the raw string; the service converts and raises
    ValidationError('priority', ...)".
  - writes a second copy of the 1-5 check -> amend: "reuse the validation helper from Session 1".
  - only tests the service -> amend: "also test the route with app.test_client()".

SESSION 3
Add an update_task function to @services/tasks.py and a PATCH /tasks/<id> route in @routes/api.py so a task's priority can be updated. Unknown task IDs must return 404 and invalid priority 422. Add tests. Run pytest -q when done.

  Amend if the plan...
  - lets PATCH change any field (title, done, user_id) -> amend scope: "only priority; a body without
    priority raises ValidationError".
  - looks up the task with TASKS[task_id] -> amend: "call get_task(task_id) so NotFoundError comes from one place".
  - tests mutate TASKS without restoring it -> amend: "restore the original priority after the test".

SESSION 4
Make POST /tasks in @routes/api.py accept an optional priority and pass it to create_task. Add route-level tests in a new tests/test_api.py using app.test_client() that check priority appears in POST, GET and PATCH responses. Run pytest -q when done.

  Amend if the plan...
  - puts route tests into tests/test_tasks.py or edits existing tests -> amend: new file tests/test_api.py only.
  - has no state reset -> amend: "add a fixture that deep-copies TASKS before each test and restores it after".
  - posts invalid priority without checking the 422 JSON body -> amend: "assert response.get_json()['error']".

WHERE DIVERGENCE USUALLY SHOWS UP (check git diff against the plan you approved):
  - Claude edits a file the plan didn't list (e.g. tests/test_tasks.py in Session 4)
  - Claude skips a step you added (e.g. the bool check, or the state-reset fixture)
  - Claude "improves" something you didn't ask for (e.g. adds sorting by priority)
-->
