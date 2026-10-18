#!/usr/bin/env python3
"""PreToolUse hook: blocks writes to protected files and directories."""
import json, sys, os

# Paths this project must never let Claude write to.
# From my CLAUDE.md Do-not-touch section and Week 5 DECOMPOSITION.md.
BLOCKED_PATHS = [
    "utils/errors.py",          # AppError hierarchy; handle_app_error depends on it
    "requirements.txt",         # CLAUDE.md: do not edit requirements.txt
    "DRILL_PROMPTS.md",         # CLAUDE.md: do not edit DRILL_PROMPTS.md
    "migrations/",              # Migrations require human review (drill test)
    ".env",                     # Secrets: hard block
    ".claude/settings.json",    # Hook config: agents must not self-modify
]

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

def is_blocked(file_path: str) -> tuple[bool, str]:
    """Return (blocked, reason) for the given file path."""
    # Claude Code sends absolute paths, so compare absolute to absolute.
    norm = os.path.normpath(os.path.abspath(file_path))
    for pattern in BLOCKED_PATHS:
        target = os.path.normpath(os.path.join(PROJECT_DIR, pattern))
        if norm == target:
            return True, f"Protected file: {pattern}"
        if pattern.endswith("/") and norm.startswith(target + os.sep):
            return True, f"Protected directory: {pattern}"
    return False, ""

def main():
    payload = json.loads(sys.stdin.read())
    tool = payload.get("tool_name", "")

    # Only inspect file-write tools
    if tool not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    file_path = (
        payload.get("tool_input", {}).get("file_path")
        or payload.get("tool_input", {}).get("path", "")
    )

    blocked, reason = is_blocked(file_path)
    if blocked:
        print(f"BLOCKED: {reason}. This file is protected by project policy.", file=sys.stderr)
        print(f"To modify {file_path}, update CLAUDE.md and remove the", file=sys.stderr)
        print("protection after team review.", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()