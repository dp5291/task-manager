# Safety Kit — task-manager (Week 8)

Four layers, from advisory to enforced:

| Layer | File | Kind |
|---|---|---|
| 1. Git conventions | `CLAUDE.md` → `## Git Conventions` | Advisory (Claude reads it every session) |
| 2. Review-and-commit command | `.claude/commands/ship.md` | Advisory steps; the approval before `git commit` is enforced by `permissions.ask` rules |
| 3a. Commit-message hook | `.githooks/commit-msg` (activated with `git config core.hooksPath .githooks`) | Enforced by git, for every commit, mine or Claude's |
| 3b. Claude Code guard hook | `.claude/hooks/guard_git.py`, registered in `.claude/settings.json` with matcher `Bash\|PowerShell` | Enforced by Claude Code, before every shell command Claude runs |

Setup note for anyone who clones the repo: `core.hooksPath` is local git config and isn't cloned. Run `git config core.hooksPath .githooks` once after cloning, or the commit-msg hook will not run.

Environment: Claude Code v2.1.314, Opus 5.5, Claude Pro login (no API key), Windows PowerShell, "manual mode" (asks before acting) for every test.

---

## `git commit` and `/ship`'s `allowed-tools` — what I decided, and what actually happened

**Decision.** `/ship` pre-approves only `git status`, `git diff`, `git ls-files`, `git add`, `git log`, `pytest -q` and `ruff check`. I left `git commit` out on purpose. Step 5 of `/ship` says "wait for my approval", but that is only text, and the model can skip it. Without a pre-approval, I expected Claude Code to show a permission prompt before every commit, so the approval gate would be enforced, not advisory. `git push` is left out for the same reason, and `guard_git.py` also blocks pushes to `main`.

**What actually happened (Test 2).** No permission prompt appeared. Claude ran one combined command, `git add GIT_POLICY.md && git commit -m "..."`, and it went straight through. I found that command in the session transcript (`dfbed2a9-….jsonl`). I checked for a saved approval: `/permissions` showed an empty Allow list, `.claude/settings.local.json` doesn't exist, user `settings.json` has no allow rules, and every `allowedTools` in `~/.claude.json` is `[]`. So leaving a tool out of `allowed-tools` doesn't guarantee a prompt. In my run, my "enforced" gate was really advisory.

**Fix.** I added explicit ask rules to `.claude/settings.json`. Claude Code always prompts for these, whatever the slash command allows:

```json
"permissions": {
  "ask": ["Bash(git commit *)", "Bash(git commit)", "PowerShell(git commit *)", "PowerShell(git commit)"]
}
```

Committed as `56d7e03 fix(hooks): cover PowerShell tool and ask before git commit`. Test 5 shows the prompt now appears.

---

## Test 1 — `/ship` stops on a planted debug statement

- **Setup:** I added `print("DEBUG list_tasks")` by hand inside `list_tasks()` in `services/tasks.py` (`git diff --stat`: `services/tasks.py | 1 +`).
- **Command:** `/ship`
- **Output:**

```
● Debug check failed. The diff adds a debug statement:

  - services/tasks.py:130 — a print( call (print("DEBUG list_tasks")) in list_tasks

  Not committing. Fix these and run /ship again.

  I stopped there, so I didn't run tests or stage anything. Once that line is removed,
  services/tasks.py has no changes left, so there's nothing else to commit.
```

- **Result:** `/ship` stopped at step 1, before running tests or staging anything. I then ran `git checkout -- services/tasks.py`, and `git status --short` printed nothing.

## Test 2 — `/ship` completes a clean commit

- **Setup:** added `GIT_POLICY.md` (untracked, the only change).
- **Command:** `/ship docs`
- **Output:**

```
Read 1 file, ran 1 shell command

● I checked GIT_POLICY.md, the only change (a new untracked file). It's 46 lines of Markdown
  with no print(/breakpoint(/pdb, no TODO or FIXME, and no commented-out code. All 102 tests
  pass (pytest -q), and ruff check services/ utils/ prints "All checks passed!"

  File to stage:
  - GIT_POLICY.md

  Proposed message:
  docs(claude): add team git policy with enforcement mechanisms

  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

  ...
  Commit with this message? (yes / edit / no)

> yes

  Committed fefcbc8
● I committed GIT_POLICY.md on main as fefcbc8 docs(claude): add team git policy with
  enforcement mechanisms. The commit-msg hook accepted the subject, and nothing was pushed.
```

```
PS> git log --oneline -3
fefcbc8 (HEAD -> main) docs(claude): add team git policy with enforcement mechanisms
eaa38ba feat(hooks): add guard_git PreToolUse hook
8d03000 feat(hooks): add conventional commit-msg git hook
```

- **Result:** all four `/ship` steps ran in order: debug check, `102 passed`, ruff clean, then one proposed message, and it waited for my "yes". It added the `Co-Authored-By` trailer itself, which matches the attribution decision in `GIT_POLICY.md`. **But no permission prompt appeared before `git commit`** (see the section above).

---

## Test 3 — commit-msg hook rejects a bad subject, accepts a good one

**Bad subject**

```
PS> git commit -m "fixed stuff"
commit-msg: rejected subject: "fixed stuff"
  Use 'type(scope): subject' or 'type: subject'; types: feat fix test refactor docs chore; no trailing period.
```

The commit was not created.

**Good subject**

```
PS> git commit -m "feat(hooks): add conventional commit-msg git hook"
[main 8d03000] feat(hooks): add conventional commit-msg git hook
 create mode 100755 .githooks/commit-msg
```

`100755` shows the hook is stored as executable, so it also runs on macOS/Linux. Claude's commit `fefcbc8` (Test 2) also passed through this hook.

---

## Test 4 — guard hook blocks forbidden commands, allows normal ones

### 4a. Direct test (piping tool-call JSON into the hook)

```
PS> '{"tool_name":"Bash","tool_input":{"command":"git push origin main"}}' | python .claude/hooks/guard_git.py; "exit $LASTEXITCODE"
BLOCKED by guard_git.py: pushing to main is not allowed; push a feature branch and merge locally
exit 2
PS> '{"tool_name":"Bash","tool_input":{"command":"git push --force origin feat/x"}}' | python .claude/hooks/guard_git.py; "exit $LASTEXITCODE"
BLOCKED by guard_git.py: force-push (--force) is not allowed
exit 2
PS> '{"tool_name":"Bash","tool_input":{"command":"git commit --no-verify -m \"feat: x\""}}' | python .claude/hooks/guard_git.py; "exit $LASTEXITCODE"
BLOCKED by guard_git.py: --no-verify would skip the commit-msg hook in .githooks/
exit 2
PS> '{"tool_name":"Bash","tool_input":{"command":"git status"}}' | python .claude/hooks/guard_git.py; "exit $LASTEXITCODE"
exit 0
```

### 4b. Claude tries the commands in a real session

| # | Prompt to Claude | What happened |
|---|---|---|
| 1 | `I am testing my git guard hook. Run exactly this command and show me the result: git push origin main` | Not run · permission denied — `PreToolUse:Bash hook error: BLOCKED by guard_git.py: pushing to main is not allowed; push a feature branch and merge locally` |
| 2 | `Run exactly this command so the hook can block it: git push --force origin main` | Not run · permission denied — `BLOCKED by guard_git.py: force-push (--force) is not allowed` |
| 3 | `Run exactly this command so the hook can block it: git commit --allow-empty --no-verify -m "chore: hook test"` | Not run · permission denied — `BLOCKED by guard_git.py: --no-verify would skip the commit-msg hook in .githooks/` |
| 4 | `Run git status and git log --oneline -3` | **Allowed** — ran normally: "You're on main, 5 commits ahead of origin/main …", last 3 commits listed |

All three forbidden commands were blocked with a one-line reason; the normal command passed through.

### 4c. Gap found during testing: the PowerShell tool

During test 1, Claude pointed out that on Windows it also has a **PowerShell tool**, and both hooks only matched `Bash`. So `git push origin main` sent through PowerShell would have bypassed `guard_git.py`. Fix (commit `56d7e03`):
- matcher changed to `"Bash|PowerShell"`
- `guard_git.py` now checks `tool_name in ("Bash", "PowerShell")`

Re-test:

```
PS> '{"tool_name":"PowerShell","tool_input":{"command":"git push origin main"}}' | python .claude/hooks/guard_git.py; "exit $LASTEXITCODE"
BLOCKED by guard_git.py: pushing to main is not allowed; push a feature branch and merge locally
exit 2
```

In a real session:

```
> Use the PowerShell tool to run exactly: git push --force origin no-such-branch
  Ran 1 shell command
  Not run · permission denied
  │ Reason: PreToolUse:PowerShell hook error: BLOCKED by guard_git.py: force-push (--force) is not allowed
```

When I asked Claude to push to `main` through PowerShell, it **refused before trying**, quoting CLAUDE.md "Never push to main or master". That's the advisory layer stopping it before the hook needed to. `guard_writes.py` still matches only `Write|Edit|MultiEdit|Bash` (see Known gaps).

## Test 5 — `git commit` now requires approval

| Prompt | Tool | Result |
|---|---|---|
| `Run exactly: git commit --allow-empty -m "chore: test ask rule"` | PowerShell | "PowerShell command … This command requires approval. Do you want to proceed? 1. Yes 2. Yes, and don't ask again for: git commit * 3. No". I declined, so no commit was made. |
| `Use the Bash tool to run exactly: git commit --allow-empty -m "chore: test ask rule"` | Bash | Stopped for approval. I declined, so it shows "Interrupted · What should Claude do instead?" and no commit was made. |
| `/ship docs` (committing `SAFETY_KIT.md`) | Bash, `git add … && git commit …` | After I typed "yes", the approval box appeared, and I picked 1. Yes. Committed `33bf825`. |
| `/ship` in the archiving worktree | Bash, `cd … && git add … && git commit …` | `Permission rule Bash(git commit *) requires confirmation for this command.` I picked 1. Yes. Committed `1b77242`. |
| `/ship` in the due-dates worktree | Bash, `cd … && git add … && git commit …` | `Permission rule Bash(git commit *) requires confirmation for this command.` I picked 1. Yes. Committed `409bdb8`. |

No empty test commit was created. Unlike Test 2, the ask rule also catches the chained `git add && git commit` that `/ship` runs, including inside the worktrees, because `.claude/settings.json` is committed and each worktree gets a copy.

---

## Rule classification

| Rule (source) | Advisory / Enforced | Why it sits here |
|---|---|---|
| Subject is `type(scope): subject` or `type: subject` with an allowed type (CLAUDE.md 1.1, hook 1.3a) | **Enforced** | `.githooks/commit-msg` rejects any other subject for every commit, mine or Claude's (Test 3). |
| Subject ≤ 72 chars, no trailing period (1.1) | **Enforced** | The same hook checks length and the trailing period. |
| Scope is one of `tasks, users, tags, api, tests, hooks, claude, db` (1.1) | Advisory | The hook accepts any lower-case scope; Claude chose `claude` in Test 2 only because it read the list in CLAUDE.md. |
| Imperative, lower-case subject; one logical change per commit (1.1) | Advisory | A regex can't judge mood or "one change"; `/ship` asks for it but the model decides. |
| Branch names `feat/<topic>` / `fix/<topic>` (1.1) | Advisory | Nothing checks branch names when they are created. |
| Run `pytest -q` and `ruff check` before every commit (1.1) | Advisory | `/ship` runs them (Test 2), but `/ship` is a prompt and a direct `git commit` skips it; no git hook runs tests. |
| Changed test gets a reason in the commit body; never loosen a test (1.1) | Advisory | Only human review of the diff can tell whether a test was weakened. |
| Never push to `main`/`master` (1.1, 1.3b) | **Enforced** (for Claude) | `guard_git.py` exits 2 for Bash and PowerShell (Tests 4b and 4c). It doesn't stop me pushing from my own terminal. |
| Never force-push (1.1, 1.3b) | **Enforced** (for Claude) | `guard_git.py` blocks `--force`, `-f`, `--force-with-lease` and `+refspec` (Tests 4b and 4c). |
| Never skip hooks: `--no-verify`, `commit -n` (1.1, 1.3b) | **Enforced** (for Claude) | `guard_git.py` blocks both (Test 4b #3), so Claude can't get around the commit-msg hook. |
| Never change `core.hooksPath` (1.1) | **Enforced** (for Claude) | `guard_git.py` blocks `git config core.hooksPath …`, `--unset` and `-c core.hooksPath=`. |
| Never edit `.githooks/` (1.1) | Advisory | `.githooks/` isn't in `guard_writes.py`'s `BLOCKED_PATHS`, so only the CLAUDE.md rule keeps Claude out of it. |
| Don't commit `tasks.db` test changes (1.1, ship.md) | Advisory | It's in CLAUDE.md and `/ship`'s constraints, but `tasks.db` isn't gitignored or blocked by a hook. |
| `/ship` stops on `print()`, `breakpoint()`, new TODO/FIXME, commented-out code (1.2) | Advisory | Claude reads the diff and decides (Test 1 caught it); a debug line it misreads would get through. |
| `/ship` stops if tests fail (1.2) | Advisory | Claude runs `pytest -q` and is told to stop; nothing technical prevents a commit after a failure. |
| `/ship` waits for my approval before committing (1.2) | **Enforced** (since `56d7e03`) | The `permissions.ask` rules for `git commit` make Claude Code prompt every time (Test 5). Leaving `git commit` out of `allowed-tools` alone did **not** (Test 2). |
| `/ship` never pushes (1.2) | **Enforced** for `main`; advisory for feature branches | `guard_git.py` blocks pushes to main; a push to a feature branch isn't pre-approved, but no ask rule covers it either. |
| commit-msg hook applies to every commit (1.3a) | **Enforced** | Git runs it for every commit in this clone once `core.hooksPath` is set; only `--no-verify` skips it, and that is blocked for Claude. |
| Guard hook checks every shell command (1.3b) | **Enforced** | Claude Code runs PreToolUse hooks before every Bash and PowerShell call; it only sees the command text, not git calls made inside a script Claude runs. |

## Known gaps (not fixed)
- `guard_writes.py` still matches only `Write|Edit|MultiEdit|Bash`, so a PowerShell `Set-Content utils/errors.py` wouldn't be caught.
- `core.hooksPath` has to be set by hand in every new clone.
- Nothing enforces scopes, branch names, or "run tests before commit" for commits I make myself in the terminal.
