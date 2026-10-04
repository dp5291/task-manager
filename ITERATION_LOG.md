# Iteration Log — task-manager CLAUDE.md

Starting point: `CLAUDE_v1.md` (snapshot taken before any Claude Code session).

<!--
HOW TO USE THIS FILE (delete these comments before submitting)
- Every [bracketed] part must be filled from YOUR real session. Do not invent output.
- After each session run:  git diff   pytest -v   ruff check services/ utils/
- Count "corrections" = every time you had to tell Claude to fix something,
  or had to fix it yourself. You need this number for the final summary.
- Start a NEW claude session for each one (/exit, then claude) so the updated
  CLAUDE.md is reloaded.
-->

## Session 1 — 2026-10-04

### Prompt used
Add error handling to the get_task function in @services/tasks.py. Do not change the function signature. Run pytest -v when done.

### What Claude did
Claude imported NotFoundError from utils/errors.py and added a check-first guard to get_task:
`if task_id not in TASKS: raise NotFoundError("Task")`, matching get_user exactly. It also added a
Google-style docstring with Args, Returns and Raises sections. The signature (`-> dict`) was unchanged,
process_order was left alone, and existing tests were not edited. pytest -v: 4 passed.
What was missing: no test verifies that NotFoundError is raised. test_get_task_invalid uses
pytest.raises(Exception), which passed before the change too (on KeyError), so the new behaviour is untested.

### Observation
The Conventions rules "Missing item: check first, then raise, like get_user" and "Raise NotFoundError or
ValidationError from utils/errors.py" were followed exactly; spelling out the one-line pattern left
nothing to guess. The Do-not-touch rule on signatures was also followed. The gap was in my own rule:
"New service functions get a test in tests/test_tasks.py" only covers new functions, so Claude had no
instruction to test a new raise added to an existing function.

### CLAUDE.md update
Changed:
- New service functions get a test in `tests/test_tasks.py`.
To:
- New service functions, and any new `raise` added to an existing one, get a NEW test in `tests/test_tasks.py` using the specific class, e.g. `pytest.raises(NotFoundError)`. Add tests; never edit existing ones.

I changed this because in Session 1 Claude added NotFoundError to get_task but no test checked it; the
existing pytest.raises(Exception) test would have passed with the old KeyError too.

**Corrections needed this session:** 0

---

## Session 2 — 2026-10-04

### Prompt used
Refactor create_task in @services/tasks.py to match the style of get_user in @services/users.py exactly. Run pytest -v when done.

### What Claude did
Claude added a Google-style docstring (Args, Returns, Raises) matching get_user, a check that raises
ValidationError("title", "cannot be empty") for a blank title, and a call to get_user(user_id) so an
unknown user raises NotFoundError("User"). The signature was unchanged. It added two new tests,
test_create_task_empty_title and test_create_task_unknown_user, using pytest.raises(ValidationError)
and pytest.raises(NotFoundError). pytest -v: 6 passed; ruff check services/ utils/: all checks passed.
What was wrong: both new tests import create_task and the error classes inside the test function body
instead of at the top of tests/test_tasks.py. Also, the title validation was copied from create_user,
not get_user, even though the prompt said "exactly" like get_user.

### Observation
The rule I added after Session 1 ("Add tests; never edit existing ones") was followed, since Claude
wrote two new tests with specific error classes, but it was followed too literally: Claude treated
the existing import line at the top of tests/test_tasks.py as off-limits and put imports inside each
test function instead. This is a case where CLAUDE.md caused the mistake rather than preventing it.
Ruff didn't catch it because my lint command only covers services/ and utils/. Claude correctly used
get_user(user_id) instead of reading USERS directly, but that came from its own reading of "Only
functions in the owning module read or write them"; no rule said it explicitly.

### CLAUDE.md update
Changed (Conventions):
- New service functions, and any new `raise` added to an existing one, get a NEW test in `tests/test_tasks.py` using the specific class, e.g. `pytest.raises(NotFoundError)`. Never modify existing test functions, but do add needed imports to the import block at the top of the file — no imports inside test functions.

Added (Architecture):
- Cross-module checks go through the other module's service function: `create_task` calls `get_user(user_id)`; never import `USERS` into `services/tasks.py`.

I changed the test rule because in Session 2 Claude read "never edit existing ones" as including the
import block and put imports inside test functions. I added the cross-module rule so the correct
behaviour Claude chose in Session 2 is written down instead of left to chance.

**Corrections needed this session:** 1 (moved the test imports to the top of tests/test_tasks.py myself)
---

## Session 3 — [date]

### Prompt used
```
Add a new function to @services/tasks.py that returns all tasks for a given user_id. Follow the same pattern as the existing functions. Add a test for it. Run pytest -v when done.
```

### What Claude did
[Function name, return type, empty-result behaviour, unknown-user behaviour, test(s) added, did it also add a route?]

<!-- WATCH FOR:
- Creates a repositories/ folder (not asked for)
- Adds a /users/<id>/tasks route in routes/api.py without being asked
- Return type: list[dict] (good) vs dict / missing hint
- User with no tasks: returns [] or raises NotFoundError? Unknown user (999): [] or NotFoundError("User")?
- Test asserts exact count for user 1 — fragile if another test calls create_task for user 1 first
  (TASKS is shared global state across tests)
- Test added in a new file instead of tests/test_tasks.py
-->

### Observation
[Which rule governed this? Followed or not? Why?]

### CLAUDE.md update (if any)
```
[exact line(s)]
```
[I added X because Claude did Y in this session.]

<!-- CANDIDATE UPDATES:
- List queries return `[]` when nothing matches and type as `-> list[dict]`; only single-item lookups raise `NotFoundError`.
- Only add routes in `routes/api.py` when the prompt asks for an endpoint.
- `TASKS` is shared across tests and mutated by `process_order`/`create_task`: tests must not depend on test order or on exact task counts that other tests can change.
-->

**Corrections needed this session:** [N]

---

## Honest failure
[Name the session where CLAUDE.md did NOT prevent a mistake. Quote the rule that should have covered it and explain why it didn't work — e.g. the rule was too general, it existed but Claude copied nearby code instead, or the case simply wasn't covered.]

## Evidence of improvement
| Session | Corrections | CLAUDE.md lines |
|---------|-------------|-----------------|
| 1 | [N] | [wc -l after session] |
| 2 | [N] | [ ] |
| 3 | [N] | [ ] |

[One or two sentences: Session 3 needed N corrections vs N in Session 1, because rules X and Y added after Sessions 1–2 were followed without prompting.]
