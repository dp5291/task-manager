# Reflection — Week 8

## 1. One problem the safety kit caught, and one it missed

**Caught:** when I planted `print("DEBUG list_tasks")` in `list_tasks`, `/ship` stopped at `services/tasks.py:130` and printed "Not committing" before running tests or staging anything. The guard hook also blocked all three forbidden commands when Claude actually ran them: push to main, `--force`, and `--no-verify`.

**Missed:** two of my "enforced" layers had holes that only showed up in testing.
- **The approval gate.** I had left `git commit` out of `/ship`'s `allowed-tools` so Claude Code would prompt before every commit. In Test 2 it didn't. Claude ran `git add GIT_POLICY.md && git commit …` as one command and it went straight through. I had to add explicit `permissions.ask` rules. After that, every `/ship` commit stopped with "Permission rule Bash(git commit *) requires confirmation".
- **The PowerShell tool.** Claude itself pointed out that on Windows it has a PowerShell tool that my `Bash`-only matchers never saw, so `git push origin main` through PowerShell would have bypassed `guard_git.py`. I fixed that one.

The kit also could not catch the `include_archived in (…)` bug, which accepted `1` and `0`. Only my `/diff` review found it.

## 2. What parallel work cost at merge time, and was it worth it

The due-dates merge was clean (151 passed). The archiving merge conflicted in all four files: `create_task`, `update_task`, `list_tasks`, the route call, and the end of both test files. Resolving it took about seven minutes (12:49 to 12:56).

Most of it was mechanical. Two parts needed real thought:
- **The route call.** Both branches passed their own flag as the **second positional argument** of `list_tasks`. If git had merged that line silently, `include_archived` could have been read as `overdue` with no test failing. Switching to keyword arguments fixed it.
- **The interaction between the two features.** I had to decide whether `?overdue=true` should show archived tasks. I decided it shouldn't, and added two tests for it.

For this pair it was worth it. The features were built side by side in about 40 minutes, and Feature B's `0`/`1` fix showed me where to look in Feature C's diff. But the merge only went well because I knew the shared function would conflict and decided the combined behaviour myself.

## 3. What I'd change before using this on my capstone

- Start with `permissions.ask` for `git commit` and test it on a chained command on day one, instead of trusting an `allowed-tools` omission.
- Add `PowerShell` to **every** hook matcher, including `guard_writes.py`, which is still Bash-only.
- Add a pre-commit git hook that runs `pytest -q`, so "tests pass before commit" becomes enforced rather than depending on `/ship`.
- Before starting parallel worktrees, agree on the shared function signature (keyword-only flags for `list_tasks`), so the merge conflict is only text, not meaning.
- Add `.githooks/` to `guard_writes.py`'s `BLOCKED_PATHS`, and add a setup script that runs `git config core.hooksPath .githooks` after cloning.
