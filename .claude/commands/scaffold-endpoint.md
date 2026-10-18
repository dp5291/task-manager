\---

description: Scaffold a new API endpoint (route + service + schema + test) for a resource and HTTP method

argument-hint: <resource> <HTTP method>, e.g. tags POST

\---



\## Goal

Scaffold one new endpoint from $ARGUMENTS. The first word is the resource name (plural, lowercase, e.g. tags) and the second is the HTTP method (GET, POST or PATCH). Create or update exactly these files:

\- Route file: routes/api.py (add one route on the existing api blueprint, path /<resource>, or /<resource>/<int:id> for PATCH)

\- Service file: services/<resource>.py (in-memory dict store plus one service function for the method)

\- Schema file: schemas/<resource>.py (a TypedDict describing one record's fields; create schemas/\_\_init\_\_.py if it does not exist)

\- Test file: tests/test\_<resource>.py



If $ARGUMENTS does not contain both a resource and a method, stop and ask instead of guessing.



\## Context

\- Canonical route pattern: the task routes. The course calls this file routes/tasks.py; in this repo they live in routes/api.py (create\_task\_route, list\_tasks\_route, update\_task\_route). Copy their shape: read the body with \_get\_json\_object(), pass raw values to ONE service function, jsonify the result, return 201 for POST.

\- Canonical service pattern: services/tasks.py (TASKS dict, create\_task, \_check\_priority) and get\_user in services/users.py: type hints, Google-style docstrings, check first then raise ValidationError/NotFoundError from utils/errors.py.

\- Errors reach the client through handle\_app\_error in routes/api.py; routes never catch them.



\## Constraints

\- No business logic in the route handler. The route only reads the request and calls the service. No validation, defaults, filtering, sorting or if-branches on field values in routes/api.py. All of that goes in services/<resource>.py.

\- Do not touch services/tasks.py, services/users.py, utils/errors.py, app.py, tests/conftest.py or any existing test file.

\- New tests go only in tests/test\_<resource>.py; if a test changes the new store, restore it with a fixture (copy.deepcopy + .clear() + .update()).

\- Do not add dependencies or edit requirements.txt.



\## Verification

\- Write a happy-path test with app.test\_client() that calls the new endpoint and asserts the correct status code (201 for POST, 200 for GET/PATCH) and the returned JSON fields.

\- Write one invalid-input test that asserts 422 and the exact error JSON with ==.

\- Run pytest -q and confirm everything passes, old and new.

\- Run ruff check services/ utils/ and confirm "All checks passed!".

\- Report the files created/changed and the test names.

