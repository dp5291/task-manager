#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash) for task-manager: enforce git rules.

Blocks, with exit code 2 and a one-line reason on stderr:
  - pushes to main or master (explicit refspec, HEAD:main, +main, :main,
    --all/--mirror, or a bare `git push` while main/master is checked out)
  - force-pushes: --force, -f (also inside -uf), --force-with-lease[=...],
    --force-if-includes, or a +refspec
  - skipping hooks: --no-verify anywhere, `git commit -n`, or changing
    core.hooksPath (with -c or git config), which would disable .githooks/
Every other command passes through untouched (exit code 0).
"""
import json
import shlex
import subprocess
import sys

PROTECTED = {"main", "master"}
OPERATORS = {"&&", "||", ";", "|", "&", "(", ")", "\n"}
# git global options that take a separate value: git -C <path> push ...
GLOBAL_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def block(reason: str) -> None:
    print(f"BLOCKED by guard_git.py: {reason}", file=sys.stderr)
    sys.exit(2)


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:  # unbalanced quotes: fall back to a plain split
        return command.split()


def git_calls(tokens: list[str]):
    """Yield (global_opts, subcommand, args) for every `git ...` in the command."""
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("git", "git.exe") or tok.endswith(("/git", "\\git", "/git.exe", "\\git.exe")):
            i += 1
            global_opts = []
            while i < len(tokens) and tokens[i].startswith("-") and tokens[i] not in OPERATORS:
                opt = tokens[i]
                global_opts.append(opt)
                if opt in GLOBAL_OPTS_WITH_VALUE and i + 1 < len(tokens):
                    global_opts.append(tokens[i + 1])
                    i += 1
                i += 1
            sub = tokens[i] if i < len(tokens) and tokens[i] not in OPERATORS else ""
            i += 1
            args = []
            while i < len(tokens) and tokens[i] not in OPERATORS:
                args.append(tokens[i])
                i += 1
            yield global_opts, sub, args
        else:
            i += 1


def current_branch(global_opts: list[str], cwd: str | None) -> str:
    where = cwd
    if "-C" in global_opts:
        where = global_opts[global_opts.index("-C") + 1]
    try:
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=where,
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def check_push(global_opts, args, cwd):
    flags = [a for a in args if a.startswith("-")]
    positional = [a for a in args if not a.startswith("-")]
    for f in flags:
        if f in ("--force", "--force-if-includes") or f.startswith("--force-with-lease"):
            block(f"force-push ({f}) is not allowed")
        if not f.startswith("--") and "f" in f[1:]:
            block(f"force-push ({f}) is not allowed")
    if "--all" in flags or "--mirror" in flags:
        block("pushing all branches would push main; push one feature branch instead")
    refspecs = positional[1:]  # positional[0] is the remote
    for spec in refspecs:
        if spec.startswith("+"):
            block(f"force-push via '+' refspec ({spec}) is not allowed")
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        dst = dst.removeprefix("refs/heads/")
        if dst in PROTECTED:
            block(f"pushing to {dst} is not allowed; push a feature branch and merge locally")
    if not refspecs:
        branch = current_branch(global_opts, cwd)
        if branch in PROTECTED:
            block(f"bare 'git push' while on {branch} would push {branch}")


def check_hooks_bypass(global_opts, sub, args):
    if "--no-verify" in args or "--no-verify" in global_opts:
        block("--no-verify would skip the commit-msg hook in .githooks/")
    if sub == "commit" and any(a.startswith("-") and not a.startswith("--") and "n" in a[1:] for a in args):
        block("'git commit -n' is --no-verify and would skip the commit-msg hook")
    for j, opt in enumerate(global_opts):
        if opt == "-c" and j + 1 < len(global_opts) and global_opts[j + 1].lower().startswith("core.hookspath"):
            block("overriding core.hooksPath would disable .githooks/")
    if sub == "config" and any(a.lower() == "core.hookspath" for a in args):
        reading = {"--get", "--get-all", "--list", "-l", "--show-origin"}
        values = [a for a in args if not a.startswith("-") and a.lower() != "core.hookspath"]
        if "--unset" in args or "--unset-all" in args or (values and not reading & set(args)):
            block("changing core.hooksPath would disable .githooks/")


def main() -> None:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        sys.exit(0)
    if payload.get("tool_name") not in ("Bash", "PowerShell"):
        sys.exit(0)
    command = (payload.get("tool_input") or {}).get("command", "")
    cwd = payload.get("cwd")
    for global_opts, sub, args in git_calls(tokenize(command)):
        check_hooks_bypass(global_opts, sub, args)
        if sub == "push":
            check_push(global_opts, args, cwd)
    sys.exit(0)


if __name__ == "__main__":
    main()