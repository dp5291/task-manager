# Justification

## Commands
I listed exact commands because task-manager has a trap: `requirements.txt` has no linter, and `ruff check .` reports existing warnings in `tests/test_tasks.py` and `routes/api.py`, so I scoped lint to `ruff check services/ utils/` and banned `ruff check . --fix`. Claude ran both checks in all three sessions. Session 2 showed the cost of that scope: ruff missed the imports Claude put inside test functions, because `tests/` isn't linted. Under a 50% cut I would keep `pytest -v` and the scoped ruff command and drop the run-app and install lines.

## Architecture
The assignment expects routes → services → repositories, but task-manager has no `repositories/` package, so I named `TASKS` and `USERS` as the data layer. Session 2 shaped this section most: Claude checked the user with `get_user(user_id)` instead of importing `USERS`, and I turned that into an explicit cross-module rule. In Session 3 Claude followed it right away, calling `get_user(user_id)` at the start of `get_tasks_for_user`. Under a 50% cut I would keep the flow line, the no-repositories line and the cross-module rule, and drop the `handle_app_error` explanation.

## Conventions
I wrote the check-first pattern out in full, `if task_id not in TASKS: raise NotFoundError("Task")`, and Session 1 reproduced it exactly, with no try/except. The test rule changed twice: Session 1 added a raise with no test checking it, so I required new tests using the specific error class, and Session 2 then put imports inside test functions, so I clarified that the top import block may be edited. Session 3 got both right on the first try. Under a 50% cut I would keep the `get_user` reference and the test rule, since `get_user` already shows the type hints and docstring layout.

## Do not touch
Each rule protects something that breaks quietly: route imports in `routes/api.py`, the existing `pytest.raises(Exception)` tests, `.message`/`.status_code` used by `handle_app_error`, and the seed IDs 1–3. Claude broke none of them in three sessions; it kept every signature and left the seed data alone. The lesson came from Session 2: "never edit existing tests" was too blunt, because Claude counted the import line as part of existing tests. If cutting in half I would keep the signature and existing-test rules and drop the `DRILL_PROMPTS.md` line.

## Team project with three developers
First, I would split the file: the shared `CLAUDE.md` committed to git holds only project facts (commands, layers, error classes, do-not-touch rules), and each developer's preferences go in a gitignored `CLAUDE.local.md`. Changes to the shared file would go through pull-request review, because Session 2 showed that one badly worded line can change Claude's output in ways nobody expected. Second, I would mark shared contracts: `utils/errors.py`, the signatures imported by `routes/api.py`, and the `TASKS`/`USERS` seed data, which Claude must flag in the PR description instead of changing quietly. Otherwise a silent change to `create_task` could break a teammate's route or tests.
