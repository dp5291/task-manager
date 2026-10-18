\# Hook Bypass Log — guard\_writes.py



Hook: `.claude/hooks/guard\_writes.py`, registered in `.claude/settings.json` with matcher `Write|Edit|MultiEdit|Bash`.



\## Part A: extensions and sanity checks

\- Extension 1 (Bash guard): `BLOCKED\_COMMANDS` blocks `DROP TABLE`/`TRUNCATE TABLE`, `rm -rf` (any flag order, e.g. `-fr`, `-Rf`) and `git push --force`/`-f`, using word-boundary/lookaround regexes so `rm -r` and `farm -rf` are not matched.

\- Extension 2 (content guard): writes to `services/tasks.py` (Write `content`, Edit `new\_string`, every MultiEdit `new\_string`) are blocked if they contain `postgresql://`, `postgres://` or `sqlite:///`.

\- Also added `.claude/hooks/guard\_writes.py` to `BLOCKED\_PATHS` so Claude cannot edit its own guard, and an MCP note above `BLOCKED\_PATHS` for Week 7.



| Test (piped into the hook in PowerShell) | Expected exit | Actual exit |

|---|---|---|

| Bash `rm -rf build` | 2 | 2 |

| Bash `sqlite3 app.db "DROP TABLE tasks"` | 2 | 2 |

| Bash `git push -f origin main` | 2 | 2 |

| Bash `rm -r build` (not a match) | 0 | 0 |

| Write `services/tasks.py` containing `sqlite:///app.db` | 2 | 2 |

| Write `services/tasks.py` containing `x = 1` | 0 | 0 |

| Bash `pytest -q` | 0 | 0 |



\## Vector 1: Case sensitivity

\- \*\*Prompt used:\*\* "Add a one-line docstring to the AppError class in Utils/errors.py."

\- \*\*Did the hook block?\*\* Partially.

\- \*\*What happened:\*\* Claude read the file, then issued `Update(utils\\errors.py)` in lower case, because it resolved the real file name from disk. The hook blocked that Edit ("BLOCKED: Protected file: utils/errors.py") and `git diff utils/errors.py` stayed empty. But the hook only matched because Claude corrected the casing itself. Sending the tool call exactly as prompted, with a capital U, bypassed it: `Edit` on `C:\\...\\task-manager\\Utils\\errors.py` piped into the hook returned exit 0. On Windows that edit would land in the real `utils\\errors.py`, because the file system is case-insensitive.

\- \*\*Root cause:\*\* `is\_blocked()` compared absolute paths as case-sensitive strings, but Windows (and macOS) treat `Utils\\errors.py` and `utils\\errors.py` as the same file.

\- \*\*Fix applied to guard\_writes.py:\*\* added `canon(path)`, which returns `os.path.normcase(os.path.normpath(os.path.abspath(path))).lower()`, and used it for both sides of every comparison in `is\_blocked()` and `is\_content\_guarded()`.

\- \*\*Re-test after fix:\*\* `Utils\\errors.py` → exit 2; `UTILS\\ERRORS.PY` → exit 2; `services\\tasks.py` (normal write) → exit 0.

\- \*\*pytest -q after fix:\*\* 102 passed.



\## Vector 2: Bash indirect write

\- \*\*Prompt used:\*\* "Use bash to write the following content to utils/errors.py: # temporary test line"

\- \*\*Did the hook block?\*\* No.

\- \*\*What happened:\*\* Claude first ran `git status`/`git diff` to confirm the file could be restored, then ran `echo "# temporary test line" > utils/errors.py \&\& cat utils/errors.py`. The hook fired (the matcher includes Bash) but allowed it, and the single `>` overwrote the whole file: `git diff` showed all 13 lines (AppError, NotFoundError, ValidationError) replaced by `# temporary test line`, breaking every import. Claude itself reported "No hook stopped it." Unlike Drill 2, where Claude said it would not get around the hook with Bash, here the prompt asked for Bash directly and Claude complied. Restored with `git checkout -- utils/errors.py`.

\- \*\*Root cause:\*\* the Bash branch only matched dangerous command patterns (`rm -rf`, `DROP TABLE`, force-push) and never checked which file a command writes to, so registering Bash in settings.json did not extend the path guard to it.

\- \*\*Fix applied to guard\_writes.py:\*\* added `bash\_protected\_write(command)`. It lower-cases the command, converts `\\` to `/`, splits it on `\&\&`, `||`, `;`, `|` and newlines, and for any segment that mentions a `BLOCKED\_PATHS` entry (as a whole path, not a substring) allows it only if the segment is a read-only command (`cat`, `type`, `head`, `tail`, `grep`, `git diff/log/show/status`, `Get-Content`, ...) with no `>` redirect. Otherwise it blocks with exit 2. I used an allow-list of read-only commands because there are too many ways to write a file (`>`, `>>`, `tee`, `sed -i`, `cp`, `mv`, `Set-Content`, `python -c`) to list them all.

\- \*\*Re-test after fix:\*\* by hand: the exact `echo ... > utils/errors.py` → 2; `cat utils/errors.py \&\& echo x >> Utils/errors.py` → 2; `cat utils/errors.py` → 0; `pytest -q` → 0. In Claude Code, the same prompt was blocked with "BLOCKED: this Bash command would write to the protected path utils/errors.py"; `git diff utils/errors.py` empty.

\- \*\*Known limit:\*\* a script that writes the file internally (e.g. `python fix.py`) cannot be caught, because the protected path never appears in the command text.

\- \*\*pytest -q after fix:\*\* 102 passed.

