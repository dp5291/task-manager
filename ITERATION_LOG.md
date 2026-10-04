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

## Session 2 — [date]

### Prompt used
```
Refactor create_task in @services/tasks.py to match the style of get_user in @services/users.py exactly. Run pytest -v when done.
```

### What Claude did
[Describe the diff. Docstring? Validation? Did it check that user_id exists? Rename parameters? Touch tests?]

<!-- WATCH FOR:
- Renames/reorders (title, user_id) -> breaks create_task_route in routes/api.py
- Docstring missing Raises:, or Raises: lists errors the code never raises
- Imports USERS directly from services.users (reaches into another module's data)
  vs calling get_user(user_id) — decide which you want and make it a rule
- Adds ValidationError for empty title (borrowed from create_user — was that "exactly get_user"?)
- Doesn't add a test for the new validation
- Touches the route in routes/api.py
-->

### Observation
[Which rule governed this? Followed or not? Why?]

### CLAUDE.md update (if any)
```
[exact line(s)]
```
[I added X because Claude did Y in this session.]

<!-- CANDIDATE UPDATES:
- To check another resource exists, call its service function (e.g. `get_user(user_id)`); never import `USERS` into services/tasks.py.
- Keep parameter names and order unchanged — `create_task_route` calls `create_task(data["title"], data["user_id"])`.
- Every new raise gets a matching test in `tests/test_tasks.py` using the specific error class, e.g. `pytest.raises(ValidationError)`.
-->

**Corrections needed this session:** [N]

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
