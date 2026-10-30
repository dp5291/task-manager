# Merge Report — due-dates + archiving into main

## Merge commands and result
```
PS> git merge --no-ff --no-edit worktree-due-dates
Merge made by the 'ort' strategy.
 routes/api.py       |  7 ++--
 services/tasks.py   | 97 ++++++++++++++++++++++++++++++++++++++++++-----------
 tests/test_api.py   | 63 ++++++++++++++++++++++++++++++++++
 tests/test_tasks.py | 73 ++++++++++++++++++++++++++++++++++++++++
 4 files changed, 218 insertions(+), 22 deletions(-)
PS> pytest -q
151 passed in 0.84s

PS> git merge --no-ff --no-edit worktree-archiving
Auto-merging routes/api.py
CONFLICT (content): Merge conflict in routes/api.py
Auto-merging services/tasks.py
CONFLICT (content): Merge conflict in services/tasks.py
Auto-merging tests/test_api.py
CONFLICT (content): Merge conflict in tests/test_api.py
Auto-merging tests/test_tasks.py
CONFLICT (content): Merge conflict in tests/test_tasks.py
Automatic merge failed; fix conflicts and then commit the result.
```

**How I resolved them:**
1. I started `claude` on `main` and asked it to explain every conflict **without editing**: show each hunk, what each side intended, and a proposed resolution.
2. It only read files (`git show :2:` / `:3:`, `Get-Content`, `git diff --stat`), and I approved each read.
3. I made the decisions below.
4. I told Claude to apply them, approved each edit, and committed the merge myself.

---

## Conflict 1 — `services/tasks.py`: `create_task` record and `update_task`
- **Due-dates side intended:** new tasks carry `"due_date": due_date`; `update_task(task_id, priority=_UNSET, due_date=_UNSET)` lets a PATCH change priority, due date, or both, and `None` clears the date.
- **Archiving side intended:** new tasks carry `"archived": False`, and a new `archive_task(task_id)` is added. The old `update_task(task_id, priority)` line inside the hunk was only archiving's unchanged copy, not a real change.
- **Resolution:** keep **both** record keys, add `archive_task` unchanged, and use the due-dates `update_task` signature and docstring.
- **Why:** the due-dates `update_task` body had already merged cleanly below the hunk, so the signature had to match it. Taking archiving's old signature would have broken every due-date update test.

## Conflict 2 — `services/tasks.py`: `list_tasks`
- **Due-dates side intended:** `list_tasks(priority, overdue, today)`, which parses `overdue` with exact checks and keeps only tasks that are not done and are due before `today`.
- **Archiving side intended:** `list_tasks(priority, include_archived)`, which parses `include_archived` with exact checks and hides archived tasks unless it is true (`task.get("archived", False)`, because seed tasks have no key).
- **Resolution (my decisions):**
  - Signature: `list_tasks(priority=None, overdue=None, include_archived=None, today=None)`.
  - Both parsing blocks stay exactly as each branch wrote them, `overdue` first. Claude suggested a new `_parse_flag` helper and **I said no**: a merge shouldn't add new code that neither branch reviewed, and that tidy-up can be a separate commit.
  - Filters run in this order: archived, then priority, then overdue.
- **Why:** this keeps both features unchanged and puts `today` last, since only tests pass it. Running the archived filter first means every other filter works only on active tasks.

## Conflict 3 — `routes/api.py`: the `list_tasks` call
```
<<<<<<< HEAD
    tasks = list_tasks(request.args.get("priority"), request.args.get("overdue"))
=======
    tasks = list_tasks(request.args.get("priority"), request.args.get("include_archived"))
>>>>>>> worktree-archiving
```
- **Due-dates side intended:** pass `?overdue=` as the second argument.
- **Archiving side intended:** pass `?include_archived=` as the second argument.
- **Resolution:**
  ```python
  tasks = list_tasks(request.args.get("priority"),
                     overdue=request.args.get("overdue"),
                     include_archived=request.args.get("include_archived"))
  ```
- **Why:** each side used the same **positional** slot for a different flag. Taking either line as it was would silently ignore one query parameter, or read `include_archived` as `overdue`. Keyword arguments remove the ambiguity. The route still does no parsing: all validation stays in the service.

## Conflict 4 — `tests/test_api.py` and `tests/test_tasks.py`: end of file
- **Due-dates side intended:** a block of due-date and overdue tests, plus the `TODAY` / `INVALID_DUE_DATES` constants.
- **Archiving side intended:** a block of archive and `include_archived` tests.
- **Resolution:** keep both blocks in full, due-dates first and then archiving. There are no duplicate test names, and each block uses only its own constants. The imports had merged cleanly.

---

## Where the features interact: my decision

**`?overdue=true` does not show archived tasks unless `include_archived=true` is also given.** An overdue list is work I still need to act on, and archived means "out of my active view".

| Query | Result |
|---|---|
| `GET /api/tasks?overdue=true` | open, past-due, not archived |
| `GET /api/tasks?overdue=true&include_archived=true` | open and past-due, including archived |

New tests for this combined behaviour:
- `tests/test_tasks.py::test_list_tasks_overdue_hides_archived_unless_included`: creates a task due `2026-06-14`, archives it, and checks it is missing from `list_tasks(overdue="true", today=TODAY)` but present with `include_archived="true"`.
- `tests/test_api.py::test_list_tasks_route_overdue_hides_archived_unless_included`: the same check through the API, with due date `"2000-01-01"`, comparing `?overdue=true` with `?overdue=true&include_archived=true`.

**Left out on purpose** (product decisions, not merge conflicts):
- `update_task` and `process_order` still work on archived tasks.
- `get_tasks_for_user` doesn't hide them.
- There is no un-archive.

## Tests changed
**None.** No existing test was changed, deleted or loosened. Claude checked the ones most at risk and I confirmed them:
- `test_archive_task_route` asserts `{**created, "archived": True}`. `created` now also contains `"due_date": None` on both sides of the comparison, so it still passes.
- `test_list_tasks_overdue_false_returns_all` compares `list_tasks(overdue="false")` with `list_tasks()`. Both hide archived tasks, so they are still equal.
- Every other `list_tasks` call in the tests passes either only `priority` by position or the flags by keyword, so adding a parameter didn't break any.

## Final test run and merge commit
```
PS> Select-String -Path routes\api.py, services\tasks.py, tests\test_api.py, tests\test_tasks.py -Pattern '^(<<<<<<<|=======|>>>>>>>)'
(no output — no conflict markers left)
PS> pytest -q
........................................................................................ [ 52%]
...............................................................................          [100%]
167 passed in 0.46s
PS> git commit -m "Merge branch 'worktree-archiving'" -m "Conflicts: create_task record, update_task signature, list_tasks, the list_tasks call in routes/api.py, and the end of both test files. Kept both features: ..."
[main 0a880a7] Merge branch 'worktree-archiving'
```

**Test count:**

| | Tests |
|---|---|
| Main after the due-dates merge | 151 |
| Archiving tests added | 14 |
| New interaction tests | 2 |
| **Total** | **167** |

`ruff check services/ utils/` printed "All checks passed!" The commit-msg hook accepted the `Merge …` subject, because the hook lets git's own merge messages through.
