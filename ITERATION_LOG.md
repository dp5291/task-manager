# Iteration Log — task-manager CLAUDE.md
 
Starting point: `CLAUDE_v1.md` (34 lines, written before any Claude Code session).
After every session I ran `git diff`, `pytest -v` and `ruff check services/ utils/`.
 
---
 
## Session 1 — 2026-10-04
 
### Prompt used
```
Add error handling to the get_task function in @services/tasks.py. Do not change the function signature. Run pytest -v when done.
```
 
### What Claude did
Claude imported `NotFoundError` from `utils/errors.py` and added a check-first guard to `get_task`:
`if task_id not in TASKS: raise NotFoundError("Task")`, matching `get_user` exactly. It added a
Google-style docstring with `Args`, `Returns` and `Raises` sections. The signature (`-> dict`) was
unchanged, `process_order` was left alone, and existing tests were not edited. pytest -v: 4 passed;
ruff check services/ utils/: all checks passed.
What was missing: no test verifies that `NotFoundError` is raised. `test_get_task_invalid` uses
`pytest.raises(Exception)`, which also passed before the change (on `KeyError`), so the new behaviour is untested.
 
### Observation
The Conventions rules "Missing item: check first, then raise, like `get_user`" and "Raise `NotFoundError`
or `ValidationError` from `utils/errors.py`" were followed exactly — spelling out the one-line pattern
left nothing to guess. The Do-not-touch rule on signatures was also followed. The gap was in my own rule:
"New service functions get a test in `tests/test_tasks.py`" only covers new functions, so Claude had no
instruction to test a new raise added to an existing function.
 
### CLAUDE.md update
Changed:
```
- New service functions get a test in `tests/test_tasks.py`.
```
To:
```
- New service functions, and any new `raise` added to an existing one, get a NEW test in `tests/test_tasks.py` using the specific class, e.g. `pytest.raises(NotFoundError)`. Add tests; never edit existing ones.
```
I changed this because in Session 1 Claude added `NotFoundError` to `get_task` but no test checked it;
the existing `pytest.raises(Exception)` test would have passed with the old `KeyError` too.
 
**Corrections needed this session:** 0
 
---
 
## Session 2 — 2026-10-04
 
### Prompt used
```
Refactor create_task in @services/tasks.py to match the style of get_user in @services/users.py exactly. Run pytest -v when done.
```
 
### What Claude did
Claude added a Google-style docstring (Args, Returns, Raises) matching `get_user`, a check that raises
`ValidationError("title", "cannot be empty")` for a blank title, and a call to `get_user(user_id)` so an
unknown user raises `NotFoundError("User")`. The signature was unchanged. It added two new tests,
`test_create_task_empty_title` and `test_create_task_unknown_user`, using `pytest.raises(ValidationError)`
and `pytest.raises(NotFoundError)`. pytest -v: 6 passed; ruff check services/ utils/: all checks passed.
What was wrong: both new tests import `create_task` and the error classes inside the test function body
instead of at the top of `tests/test_tasks.py`. Also, the title validation was copied from `create_user`,
not `get_user`, even though the prompt said "exactly" like `get_user`.
 
### Observation
The rule I added after Session 1 ("Add tests; never edit existing ones") was followed — Claude wrote two
new tests with specific error classes — but too literally: it treated the existing import line at the top
of `tests/test_tasks.py` as off-limits and put imports inside each test function instead. Here CLAUDE.md
caused the mistake rather than preventing it. Ruff didn't catch it because my lint command only covers
`services/` and `utils/`. Claude correctly used `get_user(user_id)` instead of reading `USERS` directly,
but that came from its own reading of "Only functions in the owning module read or write them" — no rule
said it explicitly.
 
### CLAUDE.md update
Changed (Conventions):
```
- New service functions, and any new `raise` added to an existing one, get a NEW test in `tests/test_tasks.py` using the specific class, e.g. `pytest.raises(NotFoundError)`. Never modify existing test functions, but do add needed imports to the import block at the top of the file — no imports inside test functions.
```
Added (Architecture):
```
- Cross-module checks go through the other module's service function: `create_task` calls `get_user(user_id)`; never import `USERS` into `services/tasks.py`.
```
I changed the test rule because in Session 2 Claude read "never edit existing ones" as including the
import block and put imports inside test functions. I added the cross-module rule so the correct
behaviour Claude chose in Session 2 is written down instead of left to chance.
 
**Corrections needed this session:** 1 (I moved the test imports to the top of `tests/test_tasks.py` myself)
 
---
 
## Session 3 — 2026-10-04
 
### Prompt used
```
Add a new function to @services/tasks.py that returns all tasks for a given user_id. Follow the same pattern as the existing functions. Add a test for it. Run pytest -v when done.
```
 
### What Claude did
Claude added `get_tasks_for_user(user_id: int) -> list[dict]` with a Google-style docstring. It calls
`get_user(user_id)` first, so an unknown user raises `NotFoundError`, then returns
`[task for task in TASKS.values() if task["user_id"] == user_id]`, which is `[]` for a user with no tasks.
It added `get_tasks_for_user` to the existing import line at the top of `tests/test_tasks.py` and wrote two
tests: `test_get_tasks_for_user_valid` (checks IDs 1 and 2 are present and 3 is not, rather than an exact
count) and `test_get_tasks_for_user_unknown_user` (`pytest.raises(NotFoundError)`). No route was added and
no `repositories/` folder was created. pytest -v: 8 passed; ruff check services/ utils/: all checks passed.
Minor gap: the docstring promises "empty if they have none", but no test covers that case — both seed users
in `USERS` own tasks, so the empty-list path is never exercised.
 
### Observation
Both Session 2 updates were followed on the first try: the import went into the top import block (no
in-function imports), and the user check went through `get_user(user_id)` as the new Architecture rule
says. The Session 1 test rule produced two tests using the specific `NotFoundError` class. Claude also
avoided an exact-count assertion even though no rule asked for it, which matters because `TASKS` is shared
state that `create_task` changes during the test run.
 
### CLAUDE.md update
Added (Conventions):
```
- List queries (e.g. `get_tasks_for_user`) return `[]` for an existing user with no tasks; test that case by creating a user with `create_user` first, not by relying on seed data.
```
I added this because in Session 3 the docstring promised an empty list but no test covered it, since every
seed user in `USERS` already has tasks.
 
**Corrections needed this session:** 0
 
---
 
## Honest failure
Session 2. CLAUDE.md already had a test rule ("Add tests; never edit existing ones"), and Claude obeyed it —
but the wording didn't say where the boundary was. Claude treated the import line at the top of
`tests/test_tasks.py` as part of "existing" tests and put `from services.tasks import create_task` inside each
new test function instead. So the rule didn't prevent the mistake; it caused it. My scoped lint command
(`ruff check services/ utils/`) also couldn't catch it, because `tests/` is outside the lint scope. The fix
was to say exactly what is protected (existing test *functions*) and what is allowed (adding to the import
block at the top).
 
## Evidence of improvement
| Session | Task | Corrections | Issues found in review | CLAUDE.md lines after |
|---------|------|-------------|------------------------|-----------------------|
| 1 | Add error handling to `get_task` | 0 | 1 — new `NotFoundError` untested | 34 |
| 2 | Refactor `create_task` | 1 | 2 — imports inside tests; extra validation beyond `get_user` | 35 |
| 3 | New `get_tasks_for_user` + tests | 0 | 1 minor — empty-list case untested | 36 |
 
Session 3 was the largest task (a new function plus tests) and needed 0 corrections, down from 1 in Session 2.
Session 1 also needed 0, but it was a two-line change. The clearer evidence is that both rules added after
Session 2 — imports at the top of `tests/test_tasks.py` and cross-module checks through `get_user` — were
followed in Session 3 without prompting, and the Session 2 mistake did not come back.