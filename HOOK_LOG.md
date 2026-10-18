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

\- \*\*Prompt used:\*\* \[ ]

\- \*\*Did the hook block?\*\* \[Yes / No / Partially]

\- \*\*What happened:\*\* \[ ]

\- \*\*Root cause (if not blocked):\*\* \[ ]

\- \*\*Fix applied to guard\_writes.py:\*\* \[ ]

\- \*\*Re-test after fix:\*\* \[ ]

\- \*\*pytest -q after fix:\*\* \[ ]



\## Vector 2: Bash indirect write

\- \*\*Prompt used:\*\* \[ ]

\- \*\*Did the hook block?\*\* \[Yes / No / Partially]

\- \*\*What happened:\*\* \[ ]

\- \*\*Root cause (if not blocked):\*\* \[ ]

\- \*\*Fix applied to guard\_writes.py:\*\* \[ ]

\- \*\*Re-test after fix:\*\* \[ ]

\- \*\*pytest -q after fix:\*\* \[ ]

