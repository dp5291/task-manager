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

## Session 1 — [date]

### Prompt used
```
Add error handling to the get_task function in @services/tasks.py. Do not change the function signature. Run pytest -v when done.
```

### What Claude did
[Describe the diff. Which exception did it raise? Did tests pass? What was correct, what was wrong?]

<!-- WATCH FOR (the correct answer looks like get_user):
    if task_id not in TASKS:
        raise NotFoundError("Task")
    return TASKS[task_id]
  plus a Google docstring with Raises: NotFoundError, and the import from utils.errors.
- Uses try/except KeyError instead of the check-first pattern
- Message is "Task 999 not found" or similar instead of NotFoundError("Task")
- Changes -> dict to -> dict | None / Optional[dict]  (counts as a signature change)
- Also "fixes" process_order even though the prompt only named get_task
- Edits test_get_task_invalid to pytest.raises(NotFoundError)  (breaks Do-not-touch rule)
- Runs ruff check . --fix and rewrites tests/routes
-->

### Observation
[Which CLAUDE.md rule governed this (quote it)? Was it followed? If not, why — was the rule too vague, missing, or buried?]

### CLAUDE.md update (if any)
```
[paste the exact line(s) you added or changed]
```
[I added X because Claude did Y in this session.]

<!-- CANDIDATE UPDATES (use only if they match what you saw):
- Only change the functions the prompt names; leave `process_order` alone unless asked.
- The return type is part of the signature: keep `-> dict`, never `-> dict | None`.
- `NotFoundError` takes the resource name only: `NotFoundError("Task")`, not a full message.
-->

**Corrections needed this session:** [N]

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
