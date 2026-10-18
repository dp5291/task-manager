\# Use this right after any Claude Code change to check the uncommitted diff stayed inside the files you allowed; do not use it to make or undo changes, or when the working tree already has unrelated edits.



\## Goal

Check the current uncommitted changes against the allowed files listed in $ARGUMENTS (space-separated repo-relative paths, e.g. routes/api.py services/tags.py tests/test\_tags.py) and report every file that was changed or created outside that list, plus any project-rule violations inside the allowed files.



\## Context

\- This is the check I ran by hand after every Week 5 subagent and Plan Mode session (git diff --stat, then reading the diff), which is where scope drift showed up.

\- Project rules to check inside the diff (from CLAUDE.md): no validation or business logic added to routes/api.py; services raise NotFoundError/ValidationError from utils/errors.py, never raw exceptions; existing tests are not edited; new 422/404 tests assert the exact error JSON with ==, not "error" in.

\- .claude/hooks/guard\_writes.py already blocks protected files; this command catches scope drift the hook cannot see.



\## Constraints

\- Read-only. Do not edit, create, stage, commit, revert or delete any file. Do not run git checkout, git restore, git reset, git stash, git add or git commit.

\- Only use git status --porcelain, git diff, git diff --stat, pytest -q and ruff check services/ utils/.

\- If $ARGUMENTS is empty, stop and ask for the list of allowed files.



\## Verification

\- Run git status --porcelain (this includes new untracked files) and compare every path against $ARGUMENTS.

\- Run pytest -q and ruff check services/ utils/ and include the result lines.

\- Finish with:

&#x20; 1. A table: file | allowed? (Yes/No) | change type (modified/new/deleted)

&#x20; 2. A list of rule violations found in the diff (file, line, rule), or "none"

&#x20; 3. A one-line verdict: IN SCOPE or OUT OF SCOPE

