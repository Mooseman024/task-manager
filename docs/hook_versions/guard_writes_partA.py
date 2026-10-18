#!/usr/bin/env python3
"""guard_writes.py, Part A version (before the Part B bypass fixes).

Install THIS version first and run the two bypass vectors against it, so
HOOK_LOG.md records what actually happened. Then swap in the final version.

Known gaps (on purpose, these are what Part B finds):
  - Path matching is case-sensitive          -> Vector 1
  - Bash branch only checks dangerous verbs,
    it never looks for protected paths       -> Vector 2
"""
import json
import os
import re
import sys

BLOCKED_PATHS = [
    "utils/errors.py",        # AppError hierarchy, never modified by agents
    ".env",                   # secrets, hard block
    ".claude/settings.json",  # hook config, agents must not self-modify
]

CONTENT_GUARDED_FILES = ["services/tasks.py"]
CONN_STRING_RE = re.compile(r"\b(?:postgres(?:ql)?(?:\+\w+)?://|sqlite:///)")

DANGEROUS_BASH = [
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "SQL DROP TABLE"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.I), "SQL TRUNCATE TABLE"),
    (re.compile(r"\brm\s+-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\b"), "rm -rf"),
    (re.compile(r"\bgit\s+push\b[^;&|\n]*\s(?:--force|-f)\b", re.I), "git force-push"),
]


def rel_path(file_path: str) -> str:
    root = os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    p = os.path.normpath(os.path.join(root, file_path))  # abs paths pass through join
    return os.path.relpath(p, root)


def is_blocked(rel: str) -> tuple[bool, str]:
    for pattern in BLOCKED_PATHS:
        if rel == os.path.normpath(pattern):
            return True, f"Protected file: {pattern}"
        if pattern.endswith("/") and rel.startswith(os.path.normpath(pattern) + "/"):
            return True, f"Protected directory: {pattern}"
    return False, ""


def block(msg: str) -> None:
    print(f"BLOCKED by guard_writes.py: {msg}", file=sys.stderr)
    sys.exit(2)


def main() -> None:
    payload = json.loads(sys.stdin.read())
    tool = payload.get("tool_name", "")
    ti = payload.get("tool_input", {})

    if tool in ("Bash", "PowerShell"):
        cmd = ti.get("command", "")
        for regex, label in DANGEROUS_BASH:
            if regex.search(cmd):
                block(f"destructive command ({label}): {cmd!r}")
        sys.exit(0)

    if tool not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    raw = ti.get("file_path") or ti.get("path", "")
    rel = rel_path(raw)
    blocked, reason = is_blocked(rel)
    if blocked:
        block(f"{reason}. This file is protected by project policy.")

    if rel in CONTENT_GUARDED_FILES:
        text = ti.get("content") or ti.get("new_string") or ""
        if CONN_STRING_RE.search(text):
            block("hardcoded connection string. Use environment variables.")
    sys.exit(0)


if __name__ == "__main__":
    main()
