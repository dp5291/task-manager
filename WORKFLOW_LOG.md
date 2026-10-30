# Workflow Log — Week 8 parallel features

Features: **B. Due dates** and **C. Archiving**. Both change how `list_tasks` / `GET /api/tasks` filters the list, so the merge had to combine two filters.

Both worktrees started from `33bf825` (main, pushed to `origin/main` first):

| Feature | Command | Branch | Folder |
|---|---|---|---|
| B. Due dates | `claude --worktree due-dates` | `worktree-due-dates` | `.claude/worktrees/due-dates` |
| C. Archiving | `claude --worktree archiving` | `worktree-archiving` | `.claude/worktrees/archiving` |

## Both worktrees active
```
PS> git worktree list
C:/Users/dhruv/OneDrive/Documents/AI Agent/task-manager/task-manager                             33bf825 [main]
C:/Users/dhruv/OneDrive/Documents/AI Agent/task-manager/task-manager/.claude/worktrees/archiving 33bf825 [worktree-archiving] locked
C:/Users/dhruv/OneDrive/Documents/AI Agent/task-manager/task-manager/.claude/worktrees/due-dates 33bf825 [worktree-due-dates] locked
```

Both sessions ran at the same time, in "manual mode" (Claude asks before every edit and command).

---

## Feature B — Due dates

### 1. Plan (plan mode)

**Prompt:**
> Feature B — due dates. Add an optional due_date to tasks: create_task and update_task in services/tasks.py accept it as an ISO date string "YYYY-MM-DD"; any other value raises ValidationError from utils/errors.py. Store it on the task (None when not given). Add GET /api/tasks?overdue=true that returns only tasks whose due_date is before today and that are not completed. Keep routes/api.py thin: the filtering goes in the service layer. Tests first, in tests/test_tasks.py and tests/test_api.py: valid date, invalid date (assert the exact 422 JSON with ==), updating due_date, and the overdue filter. Do not edit existing tests or utils/errors.py, and do not add anything about archiving. Plan only — do not write code yet.

**Clarifying questions Claude asked, and my answers:**

| Question | My answer |
|---|---|
| What should PATCH `"due_date": null` do? | **Clear the due date.** A user must be able to remove a date; only a wrong value like `"2026-13-45"` should be a 422. |
| `update_task` currently requires `priority`, so `{"due_date": "…"}` alone would fail. How should PATCH work? | **Both fields optional.** The route forwards only the keys in the body; a body with neither gets a 422. |

**First plan, summarised:**
- New `_check_due_date` that accepts only a regex-checked `YYYY-MM-DD` string that is also a real date.
- `due_date` added as a trailing optional parameter on `create_task`.
- `update_task(task_id, priority=_UNSET, due_date=_UNSET)`.
- `list_tasks(priority, overdue)` with the overdue check done against `date.today()` inside the function.
- Tests used dates relative to the real clock: yesterday, today, tomorrow.

**Change I requested:**
> Change: give list_tasks a today parameter (date | None = None, default date.today()) and use it for the overdue check, so the service tests pass a fixed date instead of depending on the real clock. Add a boundary test with a fixed date: due_date equal to today is NOT overdue. Also: after you write the tests and run pytest -q, STOP and wait for me before changing services/tasks.py or routes/api.py.

**Why:** with `date.today()` hard-wired, the overdue tests depend on the real clock and could fail if the suite runs across midnight. A fixed `today` makes them deterministic and lets me test the exact boundary, where a task due today is not overdue. The checkpoint gave me a clean failing run to record.

**Revised plan:**
- `TODAY = date(2026, 6, 15)` passed to `list_tasks(..., today=TODAY)` in the service tests.
- The API tests can't inject a date, so they use far-off dates: `"2000-01-01"` (overdue) and `"2999-12-31"` (not overdue).
- A new boundary test.
- A "⏸ CHECKPOINT: stop here" after the tests.

### 2. Tests first — failing run
```
PS> cd .claude\worktrees\due-dates; pytest -q 2>&1 | Select-Object -Last 12
FAILED tests/test_tasks.py::test_update_task_invalid_due_date[] - TypeError: ...
FAILED tests/test_tasks.py::test_update_task_invalid_due_date[20261201_1] - T...
FAILED tests/test_tasks.py::test_update_task_invalid_due_date[True] - TypeErr...
FAILED tests/test_tasks.py::test_update_task_invalid_due_date[due_date8] - Ty...
FAILED tests/test_tasks.py::test_update_task_no_fields - TypeError: update_ta...
FAILED tests/test_tasks.py::test_update_task_due_date_unknown_task - TypeErro...
FAILED tests/test_tasks.py::test_list_tasks_overdue - TypeError: create_task(...
FAILED tests/test_tasks.py::test_list_tasks_overdue_due_today_is_not_overdue
FAILED tests/test_tasks.py::test_list_tasks_overdue_with_priority - TypeError...
FAILED tests/test_tasks.py::test_list_tasks_overdue_false_returns_all - TypeE...
FAILED tests/test_tasks.py::test_list_tasks_invalid_overdue - TypeError: list...
49 failed, 102 passed in 0.71s
```

All 49 failures are new tests: 29 in `test_tasks.py` and 20 in `test_api.py`. All 102 existing tests still pass.

### 3. Implementation — passing run

Prompt: `Go ahead with Step 2 and Step 3. When done, run pytest -q and ruff check services/ utils/ and show me the results. Do not commit.`
```
pytest -q                   → 151 passed in 0.45s
ruff check services/ utils/ → All checks passed!
git status                  → M routes/api.py, M services/tasks.py, M tests/test_api.py, M tests/test_tasks.py
```

Claude fixed one thing itself during implementation: its first `overdue` check used `in (...)`, which would accept `0` and `1` because `1 == True` in Python. It switched to exact `is` / `==` checks.

### 4. Review with /diff — clean; what I checked

I read the `services/tasks.py` diff of `list_tasks` line by line:

| Line(s) | What I checked | Result |
|---|---|---|
| 157–158, 188–189 | `today: date \| None = None` with `date.today()` called **inside** the function, not as a default value (a default would be frozen at import time) | OK |
| 192 | strict `<` comparison, so a task due today is not overdue | OK |
| 193 | `not task["done"]`, so completed tasks are excluded | OK |
| 175–180 | `overdue` parsed with exact `is` / `==` checks; `1` and `0` are rejected | OK |
| 182–186 | the priority filter still runs before the overdue filter, so both combine | OK |

Nothing to correct here. The real correction was in Feature C.

### 5. Commits (via /ship)
- `/ship` summary: debug check clean, tests pass, `ruff check services/ utils/` printed "All checks passed!"
- Proposed message: `feat(tasks): add optional due_date and overdue filter` (53 chars), with a `Co-Authored-By: Claude Opus 5.5` trailer.
- Permission box: `Permission rule Bash(git commit *) requires confirmation for this command.` I picked 1. Yes.
```
PS> git log --oneline main..worktree-due-dates
409bdb8 (worktree-due-dates) feat(tasks): add optional due_date and overdue filter
```

One commit, because `/ship` runs `pytest -q` and won't commit the tests alone while they fail.

---

## Feature C — Archiving

### 1. Plan (plan mode)

**Prompt:**
> Feature C — archiving. Add archive_task(task_id) in services/tasks.py: it sets archived = True on the task (new tasks start with archived = False); an unknown id raises NotFoundError from utils/errors.py. Add POST /api/tasks/<int:task_id>/archive that returns the archived task. GET /api/tasks hides archived tasks by default and includes them with ?include_archived=true. Keep routes/api.py thin: the filtering goes in the service layer. Tests first, in tests/test_tasks.py and tests/test_api.py: archiving works, unknown id gives 404 (exact JSON with ==), default list hides archived, include_archived=true shows them. Do not edit existing tests or utils/errors.py, and do not add anything about due dates. Plan only — do not write code yet.

**First plan, summarised:**
- Seed tasks stay unchanged; the filter uses `task.get("archived", False)`.
- `include_archived` is parsed in the service: `None`/`"false"` hide archived tasks, `"true"` shows them, anything else is a 422.
- `list_tasks(priority, include_archived)`.
- `archive_task` reuses `get_task`, so an unknown id gives a 404; archiving twice is a no-op.
- 6 service tests and 5 API tests.
- Plan to commit through `/ship` as **two** commits: `test(tasks): add archiving tests`, then `feat(tasks): add archive_task and include_archived filter`.

**Change I requested:**
> Change: (1) make it one commit, not a tests-only commit first — /ship runs pytest -q and will refuse to commit while the new tests fail. (2) Add a test that the priority filter and the archive filter work together: an archived priority-2 task must not appear in list_tasks(2), but must appear in list_tasks(2, include_archived="true"). Also: after you write the tests and run pytest -q, STOP and wait for me before changing services/tasks.py or routes/api.py.

**Why:**
1. The two-commit plan contradicts my own safety kit. `/ship` stops when tests fail, so a tests-only commit could never pass.
2. Both filters now run in `list_tasks`, and nothing tested them together.

**Revised plan:**
- One commit: `feat(tasks): add task archiving with include_archived filter`.
- New `test_list_tasks_priority_and_archive_filters_combined`.
- A "⏸ CHECKPOINT: STOP here" after the tests.

### 2. Tests first — failing run
```
PS> cd .claude\worktrees\archiving; pytest -q 2>&1 | Select-Object -Last 15
=================================== ERRORS ====================================
____________________ ERROR collecting tests/test_tasks.py _____________________
ImportError while importing test module '...\.claude\worktrees\archiving\tests\test_tasks.py'.
...
tests\test_tasks.py:2: in <module>
    from services.tasks import archive_task, create_task, get_task, get_tasks_for_user, list_tasks, process_order, update_task
E   ImportError: cannot import name 'archive_task' from 'services.tasks' (...\.claude\worktrees\archiving\services\tasks.py)
=========================== short test summary info ===========================
ERROR tests/test_tasks.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.50s
```

Because `archive_task` didn't exist yet, the whole of `test_tasks.py` failed to load. Claude ran the other test files on their own and reported **4 failed, 59 passed**. One new test, `test_list_tasks_route_include_archived_true`, already passed before implementation, because nothing was hidden yet. It only starts testing something once the default filter exists.

### 3. Implementation — passing run

Prompt: `Go ahead with Step 2 and Step 3. When done, run pytest -q and ruff check services/ utils/ and show me the results. Do not commit.`
```
pytest -q                   → 114 passed in 0.51s
ruff check services/ utils/ → All checks passed!
```

### 4. Review with /diff — correction

**What /diff showed:** 4 files changed, +108 −8:
- `routes/api.py`: the new archive route
- `services/tasks.py`: `archive_task`, `"archived": False` in `create_task`, and the new `include_archived` parameter in `list_tasks`

**What I found** (`services/tasks.py`, lines 151–153):
```python
if include_archived in (None, False, "false"):
    include_archived = False
elif include_archived not in (True, "true"):
    raise ValidationError("include_archived", "must be true or false")
```
In Python `1 == True` and `0 == False`, so `list_tasks(include_archived=1)` was accepted as "true" instead of being rejected. Feature B had hit the same pattern in the other worktree.

**Correction I sent:**
> Correction from my /diff review: lines 151-153 check include_archived with `in (...)`, so 1 and 0 are accepted because 1 == True and 0 == False in Python. Use exact checks instead: accept only None, False, "false", True and "true" (use `is` for None/True/False), and raise ValidationError for anything else. Add a test that list_tasks(include_archived=1) raises ValidationError. Then run pytest -q and ruff check services/ utils/. Do not commit.

**Result:**
- The check became `include_archived is None or include_archived is False or include_archived == "false"` / `include_archived is True or include_archived == "true"` / `else: raise ValidationError(...)`.
- New `test_list_tasks_include_archived_rejects_int`, parametrized with `[1, 0]`.
```
pytest -q                   → 116 passed in 0.42s
ruff check services/ utils/ → All checks passed!
```

### 5. Commits (via /ship)
- `/ship` summary: debug check clean, `pytest -q` showed 116 passed in 0.48s, ruff printed "All checks passed!"
- Proposed message: `feat(tasks): add task archiving with include_archived filter` (60 chars), with a `Co-Authored-By` trailer.
- Permission box: `Permission rule Bash(git commit *) requires confirmation for this command.` I picked 1. Yes.
```
PS> git log --oneline main..worktree-archiving
1b77242 (worktree-archiving) feat(tasks): add task archiving with include_archived filter
```
