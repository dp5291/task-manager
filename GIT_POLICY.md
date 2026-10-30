# Git Policy — task-manager (four-person team, all using Claude Code)

Every rule names the mechanism that backs it. **Enforced** means git or Claude Code guarantees it; **Advisory** means it depends on Claude or a person following it, so human review backs it up.

## 1. Setup (once per clone)
| Rule | Mechanism |
|---|---|
| Run `git config core.hooksPath .githooks` right after cloning. | Human (README/onboarding). Without it the commit-msg hook does not run. |
| Never change or unset `core.hooksPath`. | **Claude Code hook** `guard_git.py` (Claude); human review (people). |
| `.githooks/`, `.claude/settings.json` and `.claude/hooks/` change only in a PR of their own, reviewed by a second person. | **Claude Code hook** `guard_writes.py` blocks Claude from editing the protected files; human review. |

## 2. Branches and commits
| Rule | Mechanism |
|---|---|
| Branch names: `feat/<topic>`, `fix/<topic>`, or `worktree-<name>` from `claude --worktree`. | **CLAUDE.md** (advisory); the reviewer rejects other names. |
| Commit subject: `type(scope): subject`, types `feat fix test refactor docs chore`, ≤ 72 chars, no trailing period. | **Git hook** `.githooks/commit-msg` (enforced, for people and Claude). |
| Scopes: `tasks, users, tags, api, tests, hooks, claude, db`; imperative mood; one logical change per commit. | **CLAUDE.md** + **slash command** `/ship` (advisory); human review. |
| Claude commits only through `/ship`: debug-code check, `pytest -q`, `ruff check`, then one proposed message. | **Slash command** `/ship` (advisory steps). |
| No commit happens without a person approving it. | **Permission setting**: `git commit` isn't in `/ship`'s `allowed-tools`, so Claude Code prompts every time (enforced). |
| Never skip hooks (`--no-verify`, `git commit -n`). | **Claude Code hook** `guard_git.py` (enforced for Claude); for people, it's a team rule checked in review. |

## 3. Attribution
**Decision: keep the `Co-Authored-By: Claude` trailer** on commits Claude makes. Reviewers can see which changes an agent wrote and review them as closely as a teammate's. It also matches our course's honesty rules.
| Rule | Mechanism |
|---|---|
| The trailer stays on. Nobody turns it off in the shared `.claude/settings.json` or a personal `.claude/settings.local.json` (Claude Code's `attribution` setting; older versions: `includeCoAuthoredBy`). | **Permission/settings file** (shared `.claude/settings.json`, committed); human review of settings changes. |
| The commit-msg hook checks the subject line only, so trailers in the body are allowed. | **Git hook** (by design). |

## 4. Parallel worktrees vs sequential work
| Rule | Mechanism |
|---|---|
| Use `claude --worktree <name>` for independent features that each need a few hours, e.g. archiving and due dates. Each session gets its own folder and branch, so the sessions can't overwrite each other's files. | Human decision; **Claude Code** worktree isolation. |
| Work one after the other when both changes touch the same function's core logic (e.g. two changes to `list_tasks` filtering), when one feature depends on another, or for a fix under 30 minutes. | Human decision. |
| Push `main` before starting worktrees, because worktrees branch from `origin`'s default branch. | Human. |
| `.claude/worktrees/` is never committed. | **`.gitignore`** (enforced). |
| Each worktree gets its own Claude session; finish or remove it with `git worktree remove` after the merge. | Human. |

## 5. Review and merge
| Rule | Mechanism |
|---|---|
| Nobody pushes to `main`/`master` or force-pushes. Feature branches are merged into `main` locally after review. | **Claude Code hook** `guard_git.py` blocks Claude. For people: a team rule. If we add a shared GitHub remote, branch protection on `main` would enforce it. |
| Every merge into `main` needs one human reviewer who reads the diff, not only the test result. | Human review. |
| A merge that needed **conflict resolution** needs a second reviewer who did not resolve it. The resolver writes in the merge commit body what each side intended and which behaviour was kept. | Human review; **CLAUDE.md** asks Claude to explain conflicts. Claude may propose a resolution, but a person decides. |
| A change to an **existing test's** expected value needs a one-line reason in the commit body and reviewer approval. Never delete or loosen a test to make a merge pass. | **CLAUDE.md** (advisory); human review. |
| `pytest -q` must pass on `main` after every merge. | `/ship` runs it before commits; human check after merge (advisory — no CI per course rules). |
| Do not commit `tasks.db` changes made while testing; reset with `python create_db.py`. | **CLAUDE.md** + `/ship` constraints (advisory); review. |
