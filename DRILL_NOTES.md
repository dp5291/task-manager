\# Week 6 Drill Notes



\# Drill 1: Custom Slash Command Builder



\## Phase 1: Recurring task

Error-handling audit: audit one services/ file and replace raw exceptions with AppError subclasses, following get\_user.

I chose it because I issued this prompt repeatedly: Week 4 Session 1 added NotFoundError to get\_task, and Week 5 kept adding ValidationError checks.



\## Phase 2: Command file

.claude/commands/audit-errors.md (v1 saved as audit-errors\_v1.md)



\## Phase 3: v1 run (/audit-errors services/tasks.py)

\- Scope: only services/tasks.py changed. No new test, because the command said "no file outside $ARGUMENTS", which beat the CLAUDE.md rule "every new raise gets a NEW test".

\- Pattern: process\_order changed from TASKS\[task\_id] (raw KeyError) to get\_task(task\_id) (raises NotFoundError) and got a Google-style docstring. A reasonable variation from get\_user's check-first code, but my command didn't specify it, so Claude chose.

\- Verification: pytest -q ran once -> 93 passed (same as before; no new test). Only 1 function changed, so per-function pacing wasn't really tested.



\## Phase 3: v2 changes (saved as audit-errors\_v2.md)

\- Constraints: allowed NEW tests in the matching test file (tests/test\_tasks.py / tests/test\_users.py) and required one per new raise; added "already compliant -> skip, do not rewrite"; named utils/errors.py, routes/api.py and tests/conftest.py as off-limits.

\- Context: "if a lookup function already exists in the same file (e.g. get\_task), call it instead of repeating the check".

\- Verification: "after every function you update, not only when done" + report table (function | changed / already compliant).



\## Phase 3: v2 run (/audit-errors services/tasks.py)

\- process\_order -> get\_task(task\_id) with docstring; new test test\_process\_order\_unknown\_task\_raises\_not\_found (pytest.raises(NotFoundError)); no existing tests changed.

\- The other 6 functions (get\_task, \_check\_priority, create\_task, update\_task, get\_tasks\_for\_user, list\_tasks) were reported "already compliant" and not touched.

\- pytest -q: 93 before -> 94 after; ruff check services/ utils/ clean. Claude ran ruff because of CLAUDE.md, not because the command asked.

\- Only services/tasks.py and tests/test\_tasks.py changed. Reverted afterwards with git checkout.



\## Phase 4: Canonical file (/audit-errors services/users.py), first run with v2

\- NOT "no changes": Claude changed create\_user (services/users.py +3/-4 lines... 7 lines changed) and added 2 tests in tests/test\_users.py; pytest 93 -> 95.

\- Reason: create\_user(123, ...) raised AttributeError at .strip() and create\_user("Carol", 5) raised TypeError at "@" in email; it added isinstance(..., str) checks raising the existing ValidationErrors.

\- Idempotency worked: get\_user, list\_users, get\_notification\_pref, set\_notification\_pref all "already compliant" and untouched.

\- It left max(USERS.keys()) alone (raw ValueError only if USERS were empty) because no allowed AppError class fit.

\- Root cause: my Goal said "every function that CAN raise a raw exception (... TypeError ...)". Any function can raise TypeError on wrong input types, so Claude treated adding input validation as part of the audit. The Goal was too broad, not the Constraints.



\## Phase 4: re-run with final command (narrowed Goal)

\- Change: Goal now fixes only (a) explicit raises of non-utils/errors.py exceptions and (b) direct TASKS\[...]/USERS\[...] indexing that raises KeyError; new Constraint: no new isinstance validation, list it under "Suggestions (not changed)".

\- Result: git diff --stat empty; all 5 functions "already compliant"; pytest -q 93 passed; create\_user's AttributeError/TypeError cases, get\_user(\[1]) and the empty-USERS max() case were listed as suggestions, not edited.

\## Debrief

Q1. What did I change between v1 and v2, and which prompt part?

the main changes were in Constraints (allowing new tests in the matching test file, the “already compliant → skip” rule) and Context (call get\_task if it exists). The evidence is that v1 gave 93 passed with no test, and v2 gave 94 passed with test\_process\_order\_unknown\_task\_raises\_not\_found.



Q2. CLAUDE.md vs slash command: practical difference?

CLAUDE.md loads into every session automatically and holds standing rules. A command only runs when you call it, holds a whole task recipe, and takes input through $ARGUMENTS. Your runs showed both working together: the command never mentioned ruff, but Claude ran it because CLAUDE.md says to.



Q3. Did the services/users.py run behave correctly? What does it reveal about my Constraints?

the first run changed users.py, which revealed the Goal was too broad (“can raise… TypeError”), not just the Constraints. After narrowing it, the run made zero changes and only reported suggestions.

