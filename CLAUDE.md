# task-manager

Flask API for tasks and users. Entry point `app.py` registers the `api` blueprint from `routes/api.py` under `/api`.

## Commands
- Install: `pip install -r requirements.txt` (flask, pytest), then `pip install ruff` for linting
- Run app: `python app.py` → http://127.0.0.1:5000/api/tasks/1
- Run tests: `pytest -v` — all tests in `tests/test_tasks.py` must pass before a task is done
- Lint: `ruff check services/ utils/` — must print "All checks passed!"
- Never run `ruff check . --fix`: it rewrites `tests/test_tasks.py` and `routes/api.py`, which have existing warnings that are out of scope

## Architecture
Requests flow one way: routes → services → repositories.
- `routes/api.py` — HTTP only: read the request, call one service function, `jsonify` the result. No business logic.
- `services/tasks.py`, `services/users.py` — business logic and validation.
- Repository layer: there is no `repositories/` package. Data lives in the module-level dicts `TASKS` (services/tasks.py) and `USERS` (services/users.py). Only functions in the owning module read or write them.
- Cross-module checks go through the other module's service function: `create_task` calls `get_user(user_id)`; never import `USERS` into `services/tasks.py`.
- Errors: services raise `AppError` subclasses; `handle_app_error` in `routes/api.py` turns them into `{"error": message}` JSON with the subclass's `status_code`. Routes never catch errors themselves.
- Canonical example of the full flow: `get_user_route` → `get_user` in `services/users.py` → `USERS`.

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
- Do not change the constructors in `utils/errors.py` — `handle_app_error` depends on `.message` and `.status_code`.
- Do not change the seed data in `TASKS` or `USERS` — tests rely on IDs 1–3 (e.g. task 2 is "Write report").
- Do not edit `DRILL_PROMPTS.md` or `requirements.txt`.