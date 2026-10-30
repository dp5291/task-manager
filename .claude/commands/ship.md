\---

description: Review the working tree, block debug code, run tests, then propose one conventional commit and wait for approval

argument-hint: \[optional hint for the commit scope or subject]

allowed-tools: Bash(git status \*), Bash(git diff \*), Bash(git ls-files \*), Bash(git add \*), Bash(git log \*), Bash(pytest -q\*), Bash(ruff check \*)

\---



\## Context

\- Status: !`git status --short`

\- Changes since last commit: !`git diff HEAD`

\- New untracked files: !`git ls-files --others --exclude-standard`

\- Recent subjects (match their style): !`git log --oneline -5`

\- Optional hint from me: $ARGUMENTS



\## Goal

Get the current changes into ONE focused conventional commit, but only if they are clean and the tests pass.



\## Steps (stop at the first failure)

1\. \*\*Debug check.\*\* Look only at lines this change ADDS (`+` lines in the diff above) and at the full contents of every new untracked file. Stop if you find any of:

&#x20;  - a `print(` or `breakpoint(` call, or `pdb` / `import pdb`

&#x20;  - a new `TODO` or `FIXME` comment

&#x20;  - commented-out code (a `#` line that is a Python statement, e.g. `# return task`, `# x = get\_task(1)`)

&#x20;  Report each one as `file:line — what it is`, then say "Not committing. Fix these and run /ship again." and STOP. Do not run tests or stage anything.

2\. \*\*Tests.\*\* Run `pytest -q`. If anything fails, list the failing tests and STOP.

3\. \*\*Lint.\*\* Run `ruff check services/ utils/`. If it reports problems, list them and STOP.

4\. \*\*Propose.\*\* Show the files you will stage and ONE commit message that follows `## Git Conventions` in CLAUDE.md: `type(scope): subject`, imperative, lower-case, no trailing period, 72 characters max. If the changes are really two separate things, say so and propose committing only one of them.

5\. \*\*Wait.\*\* Ask "Commit with this message? (yes / edit / no)" and do nothing until I answer yes.

6\. \*\*Commit.\*\* After yes: `git add` only the files you listed, then `git commit -m "<message>"`.



\## Constraints

\- Never use `--no-verify`, `-n`, `--amend` or `git push`. Never change `core.hooksPath`.

\- Never stage `tasks.db` or anything under `.claude/worktrees/`.

\- If `git commit` is rejected by the commit-msg hook, show the hook's message and propose a corrected subject; do not bypass it.

