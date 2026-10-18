#!/usr/bin/env python3
"""PreToolUse hook: blocks writes to protected files, dangerous shell
commands, and hardcoded connection strings in protected source files."""
import json, sys, os, re

# Paths this project must never let Claude write to.
# From my CLAUDE.md Do-not-touch section and Week 5 DECOMPOSITION.md.
# Week 7 / MCP note: MCP tools fire PreToolUse as mcp__<server>__<tool>.
# Every path below should ALSO be protected from MCP tools that write files
# (e.g. a filesystem server's write_file/edit_file): utils/errors.py,
# requirements.txt, DRILL_PROMPTS.md, .env and everything under .claude/.
# migrations/ applies too if an MCP database tool can create migration files.
BLOCKED_PATHS = [
    "utils/errors.py",                # AppError hierarchy; handle_app_error depends on it
    "requirements.txt",               # CLAUDE.md: do not edit requirements.txt
    "DRILL_PROMPTS.md",               # CLAUDE.md: do not edit DRILL_PROMPTS.md
    "migrations/",                    # Migrations require human review
    ".env",                           # Secrets: hard block
    ".claude/settings.json",          # Hook config: agents must not self-modify
    ".claude/hooks/guard_writes.py",  # The guard itself: agents must not self-modify
]

# Extension 1: shell commands Claude may never run (token-level regex, not substring).
BLOCKED_COMMANDS = [
    (re.compile(r"\b(?:DROP|TRUNCATE)\s+TABLE\b", re.IGNORECASE),
     "destructive SQL (DROP TABLE / TRUNCATE TABLE)"),
    (re.compile(r"(?<![\w-])rm\s+-[a-zA-Z]*(?:[rR][a-zA-Z]*f|f[a-zA-Z]*[rR])[a-zA-Z]*(?![\w-])"),
     "recursive force delete (rm -rf)"),
    (re.compile(r"\bgit\s+push\b[^\n;&|]*\s(?:--force(?:-with-lease)?|-f)(?![\w-])"),
     "git force-push (rewrites the commit history on GitHub)"),
]

# Extension 2: files Claude may write, but whose new content is inspected.
CONTENT_GUARDED_PATHS = ["services/tasks.py"]
CONNECTION_STRING = re.compile(r"postgres(?:ql)?://|sqlite:///", re.IGNORECASE)

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

def canon(path: str) -> str:
    """Absolute, normalized, lower-case path. Windows (and macOS) file systems
    are case-insensitive, so Utils/errors.py IS utils/errors.py on disk."""
    return os.path.normcase(os.path.normpath(os.path.abspath(path))).lower()

def is_blocked(file_path: str) -> tuple[bool, str]:
    """Return (blocked, reason) for the given file path."""
    # Claude Code sends absolute paths, so compare absolute to absolute,
    # case-insensitively.
    norm = canon(file_path)
    for pattern in BLOCKED_PATHS:
        target = canon(os.path.join(PROJECT_DIR, pattern))
        if norm == target:
            return True, f"Protected file: {pattern}"
        if pattern.endswith("/") and norm.startswith(target + os.sep):
            return True, f"Protected directory: {pattern}"
    return False, ""

def is_content_guarded(file_path: str) -> bool:
    norm = canon(file_path)
    return any(norm == canon(os.path.join(PROJECT_DIR, p)) for p in CONTENT_GUARDED_PATHS)

def written_text(tool: str, tool_input: dict) -> str:
    """The new text a Write/Edit/MultiEdit call would put into the file."""
    if tool == "Write":
        return tool_input.get("content", "")
    if tool == "Edit":
        return tool_input.get("new_string", "")
    if tool == "MultiEdit":
        return "\n".join(e.get("new_string", "") for e in tool_input.get("edits", []))
    return ""

# Vector 2 fix: Bash commands that touch a protected path.
# A segment that mentions a protected path is allowed only if it is a
# read-only command with no output redirection; anything else is a write.
READ_ONLY_COMMAND = re.compile(
    r"^\s*(?:cat|type|head|tail|less|more|grep|rg|wc|ls|dir|"
    r"git\s+(?:diff|log|show|status|blame)|get-content|select-string)\b",
    re.IGNORECASE,
)

def bash_protected_write(command: str) -> str:
    """Return the protected path a Bash command would write to, or ''."""
    cmd = command.replace("\\", "/").lower()
    for segment in re.split(r"&&|\|\||;|\||\n", cmd):
        for pattern in BLOCKED_PATHS:
            p = re.escape(pattern.lower().rstrip("/"))
            if re.search(r"(?<![\w.-])" + p + r"(?![\w-])", segment):
                if not READ_ONLY_COMMAND.match(segment) or ">" in segment:
                    return pattern
    return ""

def block(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)

def main():
    # Read bytes and decode as UTF-8 so Windows code pages don't crash on
    # characters like em dashes inside file content.
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    # Extension 1: Bash command guard
    if tool == "Bash":
        command = tool_input.get("command", "")
        for pattern, reason in BLOCKED_COMMANDS:
            if pattern.search(command):
                block(f"BLOCKED: {reason}. Command: {command}")
        protected = bash_protected_write(command)
        if protected:
            block(f"BLOCKED: this Bash command would write to the protected path {protected}. "
                  "Protected files cannot be changed through the shell either; "
                  f"ask the user to edit it by hand. Command: {command}")
        sys.exit(0)

    # Only inspect file-write tools below
    if tool not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    file_path = tool_input.get("file_path") or tool_input.get("path", "")

    blocked, reason = is_blocked(file_path)
    if blocked:
        print(f"BLOCKED: {reason}. This file is protected by project policy.", file=sys.stderr)
        print(f"To modify {file_path}, update CLAUDE.md and remove the", file=sys.stderr)
        print("protection after team review.", file=sys.stderr)
        sys.exit(2)

    # Extension 2: content guard
    if is_content_guarded(file_path) and CONNECTION_STRING.search(written_text(tool, tool_input)):
        block(f"BLOCKED: hardcoded database connection string (postgresql:// or sqlite:///) "
              f"in {file_path}. Connection strings must come from environment variables, "
              f"e.g. os.environ['DATABASE_URL'].")

    sys.exit(0)

if __name__ == "__main__":
    main()