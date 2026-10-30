# task-manager

Flask API for tasks and users. Entry point `app.py` registers the `api` blueprint from `routes/api.py` under `/api`.

## Commands
- Install: `pip install -r requirements.txt` (flask, pytest), then `pip install ruff` for linting
- Run app: `python app.py` → http://127.0.0.1:5000/api/tasks/1
- Run tests: `pytest -v` — all tests in `tests/test_tasks.py` must pass before a task is done
- Lint: `ruff check services/ utils/` — must print "All checks passed!"
- Never run `ruff check . --fix`: it rewrites `tests/test_tasks.py` and `routes/api.py`, which have existing warnings that are out of scope
- Quick check after each step: `pytest -q` — runs `tests/test_tasks.py`, `tests/test_api.py` and `tests/test_users.py`; `tests/conftest.py` resets `TASKS` between tests
- `/audit-errors <services file>`: convert raw exceptions (raw raises, direct `TASKS[...]`/`USERS[...]` indexing) to AppError subclasses one function at a time; skips already-compliant functions and only *suggests* new validation. Use after adding service code.
- `/scaffold-endpoint <resource> <METHOD>`: create a new endpoint across `routes/api.py`, `services/<resource>.py`, `schemas/<resource>.py` and `tests/test_<resource>.py`, e.g. `/scaffold-endpoint tags POST`.
- `/verify-scope <allowed files...>`: read-only check that the uncommitted diff touches only the listed files and follows project rules. Run it right after any Claude change, before committing.

## Architecture
Requests flow one way: routes → services → repositories.
- `routes/api.py` — HTTP only: read the request, call one service function, `jsonify` the result. No business logic.
- `services/tasks.py`, `services/users.py` — business logic and validation.
- Repository layer: there is no `repositories/` package. Data lives in the module-level dicts `TASKS` (services/tasks.py) and `USERS` (services/users.py). Only functions in the owning module read or write them.
- Cross-module checks go through the other module's service function: `create_task` calls `get_user(user_id)`; never import `USERS` into `services/tasks.py`.
- Errors: services raise `AppError` subclasses; `handle_app_error` in `routes/api.py` turns them into `{"error": message}` JSON with the subclass's `status_code`. Routes never catch errors themselves.
- Canonical example of the full flow: `get_user_route` → `get_user` in `services/users.py` → `USERS`.
- Layer boundary (enforced in Week 5 SA-3): `routes/api.py` only reads the request (bodies through `_get_json_object()`) and passes raw values to one `services/` function; all value validation, e.g. the `NOTIFICATION_PREFS` check in `set_notification_pref`, lives in `services/`, following `get_user_route` → `get_user` in `services/users.py`.

## Conventions
- `services/users.py` is the pattern to follow; `get_user` is the reference function.
- Type hints on every parameter and return value in `services/` and `utils/`, e.g. `def get_task(task_id: int) -> dict:`.
- Google-style docstrings with `Args:`, `Returns:`, `Raises:` on every service function (copy the layout of `get_user`).
- Raise `NotFoundError` or `ValidationError` from `utils/errors.py` — never raw `KeyError`, `ValueError`, or `Exception`.
- Missing item: check first, then raise, like `get_user`: `if task_id not in TASKS: raise NotFoundError("Task")`. No try/except KeyError.
- Bad input: `raise ValidationError("<field>", "<reason>")`, as in `create_user`.
- New service functions, and any new `raise` added to an existing one, get a NEW test in `tests/test_tasks.py` using the specific class, e.g. `pytest.raises(NotFoundError)`. Never modify existing test functions, but do add needed imports to the import block at the top of the file — no imports inside test functions.
- List queries (e.g. `get_tasks_for_user`) return `[]` for an existing user with no tasks; test that case by creating a user with `create_user` first, not by relying on seed data.

## Do not touch
- Do not change the signatures of `get_task`, `create_task`, or `process_order` — `routes/api.py` imports them by name and `tests/test_tasks.py` calls them.
- Do not edit or delete the existing tests in `tests/test_tasks.py`, including the `pytest.raises(Exception)` checks; fix the service code instead.
- Do not change the seed data in `TASKS` or `USERS` — tests rely on IDs 1–3 (e.g. task 2 is "Write report").
- Do not add keys to the `USERS` or `TASKS` seed records unless the prompt explicitly allows it, and never change existing IDs, names, emails or titles (SA-1 had to override the seed-data rule to add `notification_pref`).
- Do not edit `tests/` during a data- or service-layer step that only targets `services/users.py` or `services/tasks.py`; the new-test rule is met in the test step instead (SA-2: the new-test rule conflicted with "Do not touch tests/").
- Do not edit `tests/conftest.py` from a feature's test step unless asked; put that feature's reset fixture in its own test file, e.g. `restore_users` in `tests/test_users.py` (SA-4).

## Hooks
`.claude/hooks/guard_writes.py` is a PreToolUse hook, registered in `.claude/settings.json` with matcher `Write|Edit|MultiEdit|Bash`, that blocks a tool call before it runs by exiting with code 2 (its stderr message is shown to Claude). It blocks any write to the paths in `BLOCKED_PATHS` (`utils/errors.py`, `requirements.txt`, `DRILL_PROMPTS.md`, `migrations/`, `.env`, `.claude/settings.json` and the hook itself), matched case-insensitively on absolute paths, including Bash commands that write to them (`>`, `tee`, `sed -i`, `cp`, `Set-Content`, ...). It also blocks Bash commands matching `BLOCKED_COMMANDS` (`DROP`/`TRUNCATE TABLE`, `rm -rf`, `git push --force`) and writes to `services/tasks.py` that contain a `postgresql://` or `sqlite:///` connection string. To add a rule, edit the hook by hand (Claude is blocked from editing it): add a repo-relative path to `BLOCKED_PATHS`, a `(re.compile(r"..."), "reason")` pair to `BLOCKED_COMMANDS`, or a path to `CONTENT_GUARDED_PATHS`. Then pipe a sample call into it, e.g. `'{"tool_name":"Write","tool_input":{"file_path":"<path>","content":"x"}}' | python .claude/hooks/guard_writes.py; $LASTEXITCODE`, confirm exit 2 for the blocked case and 0 for a normal write, and run `pytest -q` before committing.

## Git Conventions
- Commit subject: `type(scope): subject`. Types: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`. Scopes: `tasks`, `users`, `tags`, `api`, `tests`, `hooks`, `claude`, `db` (e.g. `feat(tasks): add due_date to create_task`).
- Subject: imperative ("add", not "added"), lower-case after the colon, no trailing period, 72 characters max; one logical change per commit.
- Branches: `feat/<topic>` or `fix/<topic>` (e.g. `feat/task-archiving`); `claude --worktree <name>` branches named `worktree-<name>` are fine for feature work.
- Before every commit run `pytest -q` (all tests must pass) and `ruff check services/ utils/`; commit through `/ship`.
- A test whose expected value must change after a merge gets a one-line reason in the commit body; never delete or loosen it.
- Never push to `main` or `master`; feature branches are merged into `main` locally after review.
- Never force-push (`--force`, `-f`, `--force-with-lease`) or skip hooks (`--no-verify`, `git commit -n`).
- Never change `core.hooksPath` or edit `.githooks/`; `.githooks/commit-msg` enforces the subject format.
- Do not commit `tasks.db` changes made while testing; reset it with `python create_db.py`.