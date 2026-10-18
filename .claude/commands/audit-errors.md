\## Goal

Audit $ARGUMENTS for missing AppError handling. Only fix two things: (a) an explicit raise of an exception that is not from utils/errors.py, and (b) direct indexing such as TASKS\[task\_id] or USERS\[user\_id] that raises a raw KeyError for an unknown ID. Replace them with the appropriate AppError subclass from utils/errors.py.



\## Context

\- Canonical error-handling pattern: get\_user in services/users.py (check first, then raise NotFoundError("User")).

\- AppError hierarchy: utils/errors.py (AppError, NotFoundError, ValidationError).

\- Data lives in the module-level dicts TASKS and USERS; indexing them directly (TASKS\[task\_id]) raises a raw KeyError.

\- If a lookup function already exists in the same file (e.g. get\_task raises NotFoundError("Task")), call it instead of repeating the check.



\## Constraints

\- Only edit $ARGUMENTS, plus NEW tests in its matching test file (tests/test\_tasks.py for services/tasks.py, tests/test\_users.py for services/users.py). Do not modify utils/errors.py, routes/api.py, tests/conftest.py or any other file.

\- If a function already raises only NotFoundError/ValidationError and its docstring lists them under Raises:, skip it. Do not rewrite or reformat it; report it as "already compliant".

\- Every new raise gets one NEW test using the specific class, e.g. pytest.raises(NotFoundError). Do not edit existing tests.

\- Do not add new AppError subclasses; use only existing ones.

\- Preserve all existing function signatures.

\- Do not add new input-type validation (isinstance checks) to functions that have neither (a) nor (b). If you notice inputs that could crash with a wrong type, list them under "Suggestions (not changed)" in your report instead of editing.



\## Verification

Run pytest -q after every function you update, not only when done. All existing tests must still pass before you move to the next function. When finished, report a table: function | changed / already compliant, and the final pytest output.

