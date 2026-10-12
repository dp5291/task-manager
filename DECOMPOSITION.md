# Subagent Decomposition — User notification preferences

Feature: a user's `notification_pref` is `email`, `sms` or `none` (default `none`).
`PATCH /users/<id>/notifications` updates it (invalid value → `ValidationError`, 422),
`GET /users/<id>/notifications` returns it, and the user list and user detail responses include it.

Mapping to this codebase (decided before starting):
- "User model / nullable column" → a `notification_pref` key on every record in `USERS` (`services/users.py`).
  Seed users and new users default to the string `"none"`; a record without the key, or with `None`, is read as `"none"`.
- "Existing user list endpoint" → task-manager only has `GET /users/<id>`, so SA-2/SA-3 add `list_users()` and `GET /users`.
- Each subagent is a fresh Claude Code session (`/clear` between them). `pytest -q` is run after each one.

---

## SA-1: Data layer

| Field | Value |
|---|---|
| Input | `services/users.py`, `CLAUDE.md` |
| Task | Add a `notification_pref` key (default `"none"`) to every `USERS` record and to records made by `create_user`, plus a `NOTIFICATION_PREFS` constant. |
| Output | `services/users.py` (data only: `USERS`, `create_user`'s record dict, new constant) |
| Constraint | Do not touch `routes/api.py`, `services/tasks.py`, `utils/errors.py` or anything in `tests/`. Do not add new functions to `services/users.py`. Do not change existing seed IDs, names or emails. |
| Hand-off | Every `USERS` record has `"notification_pref": "none"`; `NOTIFICATION_PREFS = ("email", "sms", "none")` exists in `services/users.py`. |

**Prompt (paste exactly):**
```
In @services/users.py, add a module-level constant NOTIFICATION_PREFS = ("email", "sms", "none"). Add "notification_pref": "none" to every record in USERS and to the record created by create_user. This is the only change to seed data you are allowed to make: keep all IDs, names and emails the same. Do not add new functions. Do not touch routes/api.py, services/tasks.py, utils/errors.py or anything in tests/. Run pytest -q when done.
```

**Result:** pytest -q → 79 passed (no new tests expected). Fix: none. Only `services/users.py` changed (+5/−3): `NOTIFICATION_PREFS: tuple[str, ...] = ("email", "sms", "none")` added (Claude added the type hint on its own, following the CLAUDE.md type-hint rule), `"notification_pref": "none"` added to users 1 and 2 and to `create_user`'s record. No new functions; IDs, names and emails unchanged.

---

## SA-2: Service layer

| Field | Value |
|---|---|
| Input | `services/users.py`, `utils/errors.py`, `CLAUDE.md` |
| Task | Add `list_users()`, `get_notification_pref(user_id)` and `set_notification_pref(user_id, pref)` to the user service, with validation. |
| Output | `services/users.py` (new functions only) |
| Constraint | Do not touch `routes/api.py`, `services/tasks.py`, `utils/errors.py` or anything in `tests/`. Do not change `USERS` seed data or `NOTIFICATION_PREFS`. Look users up through `get_user()`. |
| Hand-off | `list_users() -> list[dict]`; `get_notification_pref(user_id: int) -> str`; `set_notification_pref(user_id: int, pref: str) -> dict` (returns the updated user). Unknown user → `NotFoundError("User")`; bad value → `ValidationError("notification_pref", "must be one of: email, sms, none")`. |

**Prompt (paste exactly):**
```
In @services/users.py, add three functions following the get_user pattern (type hints, Google-style docstrings, check-then-raise): list_users() -> list[dict] returning all users; get_notification_pref(user_id: int) -> str returning the user's notification_pref, treating a missing or None value as "none"; and set_notification_pref(user_id: int, pref: str) -> dict that updates the user and returns the updated record. Look users up with get_user so unknown IDs raise NotFoundError. If pref is not in NOTIFICATION_PREFS, raise ValidationError("notification_pref", "must be one of: email, sms, none"). Do not touch routes/api.py, services/tasks.py, utils/errors.py, anything in tests/, the USERS seed data or NOTIFICATION_PREFS. Run pytest -q when done.
```

**Result:** pytest -q → 79 passed (no new tests expected). Fix: none. Only `services/users.py` changed (+46, nothing modified): `list_users() -> list[dict]`, `get_notification_pref(user_id: int) -> str` (returns "none" when the value is missing or None) and `set_notification_pref(user_id: int, pref: str) -> dict`, all with Google-style docstrings. Both preference functions call `get_user()`, so unknown IDs raise `NotFoundError`; the user lookup runs before the value check, so an unknown user gives 404 even with a bad value. Note: the CLAUDE.md rule "any new `raise` … gets a NEW test" conflicted with this subagent's "Do not touch tests/" constraint; Claude followed the constraint, leaving the new `ValidationError` untested until SA-4.

---

## SA-3: API layer

| Field | Value |
|---|---|
| Input | `routes/api.py`, `services/users.py` (read only), `CLAUDE.md` |
| Task | Add `GET /users`, `GET /users/<id>/notifications` and `PATCH /users/<id>/notifications` routes that call the SA-2 functions. |
| Output | `routes/api.py` |
| Constraint | Do not touch `services/users.py`, `services/tasks.py`, `utils/errors.py` or anything in `tests/`. No validation logic in `routes/api.py`: pass the raw value to `set_notification_pref` and let `handle_app_error` turn errors into JSON. |
| Hand-off | `GET /api/users` → 200, list of users each with `notification_pref`. `GET /api/users/<id>/notifications` → 200 `{"user_id": id, "notification_pref": "..."}`. `PATCH /api/users/<id>/notifications` with JSON `{"notification_pref": "..."}` → 200 updated user; bad value → 422; unknown user → 404. |  A missing or non-JSON body → 422 via `_get_json_object()`.

**Prompt (paste exactly):**
```
In @routes/api.py, add three routes using the functions already in @services/users.py: GET /users returns jsonify(list_users()); GET /users/<int:user_id>/notifications returns {"user_id": user_id, "notification_pref": get_notification_pref(user_id)}; PATCH /users/<int:user_id>/notifications reads the body with the existing _get_json_object() helper, takes notification_pref from it and returns jsonify(set_notification_pref(user_id, value)). Put no validation in the routes: pass the raw value to the service and let handle_app_error produce the 404/422 responses. Do not touch services/users.py, services/tasks.py, utils/errors.py or anything in tests/. Run pytest -q when done.
```

**Result:** pytest -q → 79 passed (no new tests expected). Fix: none. Only `routes/api.py` changed (+14/−1): imported `list_users`, `get_notification_pref`, `set_notification_pref`; added `GET /users`, `GET /users/<id>/notifications` (returns `{"user_id", "notification_pref"}`) and `PATCH /users/<id>/notifications`, which reads the body with `_get_json_object()` and passes `data.get("notification_pref")` straight to the service. No validation in the routes and no `NOTIFICATION_PREFS` import. The existing `GET /users/<id>` needed no change: it already returns `notification_pref` because SA-1 added the key to every `USERS` record.

---

## SA-4: Tests

| Field | Value |
|---|---|
| Input | `services/users.py`, `routes/api.py`, `app.py`, `CLAUDE.md` (all read only) |
| Task | Write service-level and route-level tests for the notification preference feature. |
| Output | `tests/test_users.py` (new file) |
| Constraint |Do not touch `services/`, `routes/`, `utils/`, `app.py`, `tests/test_tasks.py` or `tests/conftest.py`. If a test fails because of a bug in the code, stop and report it instead of fixing the code. |
| Hand-off | Final artifact: `pytest -q` passes, covering default `"none"`, valid update, invalid value → 422, unknown user → 404, and `notification_pref` in `GET /users` and `GET /users/<id>`. |

**Prompt (paste exactly):**
```
Create tests/test_users.py covering the notification preference feature. Service tests: seed users default to "none"; set_notification_pref accepts "email", "sms" and "none"; an invalid value raises ValidationError; an unknown user raises NotFoundError. Route tests using app.test_client() from app.py: GET /api/users and GET /api/users/1 include notification_pref; GET /api/users/1/notifications returns the preference; PATCH /api/users/1/notifications with {"notification_pref": "email"} returns 200; an invalid value returns 422; user 999 returns 404. Use a pytest fixture that deep-copies USERS before each test and restores it afterwards so tests do not depend on order. Do not touch services/, routes/, utils/, app.py, tests/test_tasks.py or tests/conftest.py. If a test fails because of a bug in the code, stop and tell me instead of changing the code. Run pytest -q when done.
```

**Result:** pytest -q → 93 passed (14 new). Fix: none. Only `tests/test_users.py` was created (+87). The `USERS` fixture is autouse in the test file itself (not conftest.py, which was off-limits) and restores in place with `copy.deepcopy` + `USERS.clear()` + `USERS.update(snapshot)`. Every case listed in the prompt is covered. Gaps: no test for `get_notification_pref` returning "none" when the value is missing/None (SA-2 hand-off), and none for a missing/non-JSON PATCH body returning 422 (SA-3 hand-off); the 422/404 tests only assert `"error" in` the JSON, not the exact message.

---

## Divergence

### Did Claude follow the constraint field for every subagent?
Yes. `git diff --stat` after each subagent showed only the file in its Output field: SA-1 and SA-2 only `services/users.py`, SA-3 only `routes/api.py`, SA-4 only the new `tests/test_users.py`. The closest call was SA-2: my Week 4 CLAUDE.md says "any new `raise` … gets a NEW test in `tests/test_tasks.py`", but SA-2's constraint said "Do not touch tests/". Claude followed the constraint, so `set_notification_pref`'s `ValidationError` had no test until SA-4. In SA-4, the natural place for the `USERS` fixture was next to the `TASKS` one in `tests/conftest.py`, but because that file was in the constraint, Claude put a second autouse fixture in `tests/test_users.py` instead.

### Did any subagent's output break the next subagent's assumption? How did you recover?
Nothing broke, and pytest -q stayed green after every subagent (79, 79, 79, 93), so no recovery was needed. Each hand-off matched exactly: SA-3 imported `list_users`, `get_notification_pref` and `set_notification_pref` with the signatures SA-2 produced, and the existing `GET /users/<id>` returned `notification_pref` with no route change because SA-1 had added the key to every `USERS` record. The real problem was the opposite of a break: hand-offs that never reached the test subagent. SA-2 promised a missing/None value reads as "none", and SA-3 promised a missing or non-JSON body returns 422 through `_get_json_object()`, but the SA-4 prompt didn't list either case, so neither is tested.

### Would you write the decomposition differently a second time?
Yes, in three ways. First, I would paste every earlier hand-off line into the SA-4 prompt, or have each subagent write its own tests, so promised behaviour can't silently go untested. Second, I would require exact error bodies in the SA-4 prompt (e.g. `{"error": "Invalid notification_pref: must be one of: email, sms, none"}`), because the `==` rule I amended into Task 1 Sessions 4 and 5 was not in CLAUDE.md and came back as `"error" in`. Third, I would merge SA-1 into SA-2, since both edit only `services/users.py`, and allow SA-4 to edit `tests/conftest.py` so the `USERS` and `TASKS` reset fixtures live in one place.
