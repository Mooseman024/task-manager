#!/usr/bin/env python3
"""PreToolUse hook for task-manager.

One script, three guards:
  1. Path guard     Blocks Write/Edit/MultiEdit/NotebookEdit calls on protected
                    paths, AND blocks Bash commands that write to those paths
                    (redirects, tee, sed -i, cp/mv, interpreter one-liners...).
  2. Bash guard     Blocks destructive shell commands: DROP TABLE, TRUNCATE TABLE,
                    rm -rf (and PowerShell Remove-Item -Recurse -Force), git
                    force-push, git reset --hard.
  3. Content guard  Blocks writes to CONTENT_GUARDED_FILES whose new content
                    contains a hardcoded database connection string.

Exit 0 = allow. Exit 2 = block; stderr is shown to Claude as feedback.

To add a rule:
  - Protect a file or directory: add it to BLOCKED_PATHS (trailing "/" = dir).
  - Block a shell command: add (compiled regex, label) to DANGEROUS_BASH.
  - Content-check another file: add it to CONTENT_GUARDED_FILES.
Then add a case to tests/test_guard_writes.py and run pytest -q.
"""
import json
import os
import re
import shlex
import sys

# ── Paths Claude must never write to ────────────────────────────────────────
# Relative to the project root. Matching is case-insensitive and works on
# absolute paths, ./ prefixes, and ../ traversal (all normalized first).
#
# Week 7 note (MCP): tool calls named mcp__<server>__<tool> also fire
# PreToolUse. Rules marked [MCP] should apply to them too, since a filesystem
# or GitHub MCP server could write these files without using Write/Edit/Bash.
BLOCKED_PATHS = [
    "utils/errors.py",        # [MCP] AppError hierarchy, never modified by agents
    ".env",                   # [MCP] secrets, hard block (none today; guards the future)
    ".claude/settings.json",  # [MCP] hook config, agents must not self-modify
    ".claude/hooks/",         # [MCP] the guard itself, agents must not self-modify
]

# ── Files Claude MAY write, but whose content is inspected ──────────────────
CONTENT_GUARDED_FILES = [
    "services/tasks.py",
]

# postgresql://, postgresql+psycopg2://, postgres://, sqlite:///
CONN_STRING_RE = re.compile(r"\b(?:postgres(?:ql)?(?:\+\w+)?://|sqlite:///)", re.I)

# ── Destructive shell commands (word-boundary regex) ────────────────────────
# rm -rf is handled separately at the token level in check_rm().
DANGEROUS_BASH = [
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "SQL DROP TABLE"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.I), "SQL TRUNCATE TABLE"),
    # Stack-specific: the repo lives on GitHub (Mooseman024/task-manager) and
    # graded history must not be rewritten.
    (re.compile(r"\bgit\s+push\b[^;&|\n]*\s(?:--force(?:-with-lease)?|-f)\b", re.I),
     "git force-push (rewrites the submitted history on GitHub)"),
    (re.compile(r"\bgit\s+reset\s+[^;&|\n]*--hard\b", re.I),
     "git reset --hard (discards uncommitted work)"),
]

REDIRECTS = {">", ">>", ">|", "&>", "&>>", "1>", "2>"}
WRAPPERS = {"sudo", "env", "nohup", "time", "command", "exec", "xargs"}
TOUCH_ALL_ARGS = {"tee", "touch", "truncate", "rm", "rmdir", "mkdir", "chmod",
                  "chown", "shred", "unlink", "mv", "patch", "del", "erase",
                  # PowerShell cmdlets and aliases (Windows)
                  "set-content", "add-content", "out-file", "new-item",
                  "remove-item", "move-item", "clear-content", "ri", "ni",
                  "sc", "ac", "move", "mi"}
DEST_ONLY = {"cp", "install", "ln", "rsync", "copy", "copy-item", "cpi"}
IN_PLACE = {"sed", "perl", "ruby"}           # writers when given -i
INTERPRETERS = {"python", "python3", "perl", "ruby", "node"}
SHELLS = {"bash", "sh", "zsh", "dash"}
GIT_WRITERS = {"checkout", "restore", "rm", "mv", "apply"}


# ── Path helpers ────────────────────────────────────────────────────────────
def project_root() -> str:
    return os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def normalize(path: str, cwd: str | None = None) -> str:
    """Return the path relative to the project root, normalized and lowercased."""
    if not path:
        return ""
    p = os.path.expanduser(path.strip().replace("\\", "/"))
    root = project_root()
    if not os.path.isabs(p):
        p = os.path.join(cwd or root, p)
    p = os.path.normpath(p)
    try:
        rel = os.path.relpath(p, root)
    except ValueError:  # different drive on Windows
        rel = p
    return rel.replace("\\", "/").lower()


def is_blocked(rel: str) -> tuple[bool, str]:
    for pattern in BLOCKED_PATHS:
        pat = pattern.lower().rstrip("/")
        if pattern.endswith("/"):
            if rel == pat or rel.startswith(pat + "/"):
                return True, f"Protected directory: {pattern}"
        elif rel == pat:
            return True, f"Protected file: {pattern}"
    return False, ""


def is_content_guarded(rel: str) -> bool:
    return rel in (f.lower() for f in CONTENT_GUARDED_FILES)


def block(msg: str) -> None:
    print(f"BLOCKED by guard_writes.py: {msg}", file=sys.stderr)
    sys.exit(2)


# ── Bash parsing ────────────────────────────────────────────────────────────
def tokenize(command: str) -> list[list[str]] | None:
    """Split a shell command into segments (one per simple command).

    Returns None if the command cannot be parsed (e.g. unbalanced quotes).
    """
    segments: list[list[str]] = []
    for line in command.splitlines():
        # Windows paths (utils\errors.py) would be eaten as POSIX escapes;
        # turn path-style backslashes into "/" but keep \" and \' escapes.
        line = re.sub(r"\\(?=[A-Za-z0-9_.])", "/", line)
        try:
            lex = shlex.shlex(line, posix=True, punctuation_chars=";&|()<>")
            lex.whitespace_split = True
            tokens = list(lex)
        except ValueError:
            return None
        current: list[str] = []
        for t in tokens:
            if t in {";", "&&", "||", "|", "&", "(", ")"}:
                if current:
                    segments.append(current)
                current = []
            else:
                current.append(t)
        if current:
            segments.append(current)
    return segments


def strip_wrappers(argv: list[str]) -> list[str]:
    i = 0
    while i < len(argv):
        tok = argv[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok) or os.path.basename(tok) in WRAPPERS:
            i += 1
            continue
        if tok.startswith("-") and i > 0:  # flags belonging to a wrapper (sudo -u x)
            i += 1
            continue
        break
    return argv[i:]


def code_mentions_protected(code: str) -> list[str]:
    """Paths from BLOCKED_PATHS / CONTENT_GUARDED_FILES appearing in inline code."""
    low = code.lower().replace("\\", "/")
    hits = []
    for p in BLOCKED_PATHS + CONTENT_GUARDED_FILES:
        if p.lower().rstrip("/") in low:
            hits.append(p)
    return hits


def write_targets(segment: list[str], depth: int = 0) -> list[str]:
    """Paths this simple command would write, move, or delete."""
    targets: list[str] = []

    # 1. Redirections: anything after >, >>, 2>, &> ...
    argv: list[str] = []
    i = 0
    while i < len(segment):
        tok = segment[i]
        if tok in REDIRECTS or (tok and set(tok) <= set(">&|") and ">" in tok):
            if i + 1 < len(segment):
                targets.append(segment[i + 1])
            i += 2
            continue
        if tok in {"<", "<<", "<<<"}:
            i += 2
            continue
        argv.append(tok)
        i += 1

    argv = strip_wrappers(argv)
    if not argv:
        return targets
    cmd = os.path.basename(argv[0]).lower()
    args = argv[1:]
    plain = [a for a in args if not a.startswith("-")]

    if cmd in TOUCH_ALL_ARGS:
        targets += plain
    elif cmd in DEST_ONLY and plain:
        targets.append(plain[-1])
    elif cmd == "dd":
        targets += [a[3:] for a in args if a.startswith("of=")]
    elif cmd in IN_PLACE and any(a.startswith("-i") or a == "--in-place" for a in args):
        targets += plain
    elif cmd == "git" and args and args[0] in GIT_WRITERS:
        targets += [a for a in args[1:] if not a.startswith("-")]
    elif cmd in INTERPRETERS and any(a in ("-c", "-e") for a in args):
        # Can't tell read from write inside inline code; be conservative.
        targets += code_mentions_protected(" ".join(args))
    elif cmd in SHELLS and "-c" in args and depth < 3:
        idx = args.index("-c")
        if idx + 1 < len(args):
            for seg in tokenize(args[idx + 1]) or []:
                targets += write_targets(seg, depth + 1)
    return targets


def check_rm(segment: list[str]) -> bool:
    """True if this segment is rm with both recursive and force flags."""
    argv = strip_wrappers([t for t in segment if t not in REDIRECTS])
    if not argv:
        return False
    cmd = os.path.basename(argv[0]).lower()
    if cmd in ("remove-item", "ri", "del", "erase", "rd", "rmdir"):
        # PowerShell: Remove-Item -Recurse -Force (any case, -r/-fo abbreviations)
        flags = {a.lower() for a in argv[1:] if a.startswith("-")}
        rec = any(f in ("-recurse", "-r", "-rec") for f in flags)
        frc = any(f in ("-force", "-fo") for f in flags)
        return rec and frc
    if cmd != "rm":
        return False
    recursive = force = False
    for a in argv[1:]:
        if a in ("--recursive",):
            recursive = True
        elif a in ("--force",):
            force = True
        elif a.startswith("-") and not a.startswith("--"):
            recursive |= "r" in a or "R" in a
            force |= "f" in a
    return recursive and force


# ── Guards ──────────────────────────────────────────────────────────────────
def guard_file_tool(tool: str, tool_input: dict, cwd: str | None) -> None:
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path", "")
    rel = normalize(raw, cwd)

    blocked, reason = is_blocked(rel)
    if blocked:
        block(f"{reason}. {raw} is protected by project policy. To change it, "
              "a human must edit it after team review.")

    if is_content_guarded(rel):
        if tool == "Write":
            texts = [tool_input.get("content", "")]
        elif tool == "Edit":
            texts = [tool_input.get("new_string", "")]
        elif tool == "MultiEdit":
            texts = [e.get("new_string", "") for e in tool_input.get("edits", [])]
        else:
            texts = [tool_input.get("new_source", "")]
        for text in texts:
            if CONN_STRING_RE.search(text or ""):
                block(f"{raw} would contain a hardcoded database connection string. "
                      "Connection strings must come from environment variables "
                      "(e.g. os.environ['DATABASE_URL'] via app config), never literals.")


def guard_bash(tool_input: dict, cwd: str | None) -> None:
    command = tool_input.get("command", "") or ""

    for regex, label in DANGEROUS_BASH:
        if regex.search(command):
            block(f"destructive command ({label}) is not allowed: {command!r}")

    segments = tokenize(command)
    if segments is None:
        # Unparseable: fall back to a conservative substring check.
        if code_mentions_protected(command) and re.search(r">|\btee\b|-i\b|\bmv\b|\bcp\b", command):
            block("could not parse this command and it appears to write a protected path.")
        if re.search(r"\brm\s+-\w*[rR]\w*f|\brm\s+-\w*f\w*[rR]", command):
            block("rm -rf is not allowed.")
        return

    for seg in segments:
        if check_rm(seg):
            block(f"rm -rf (recursive force delete) is not allowed: {command!r}")
        for target in write_targets(seg):
            rel = normalize(target, cwd)
            blocked, reason = is_blocked(rel)
            if blocked:
                block(f"{reason}. This Bash command would write to it: {command!r}. "
                      "Protected files cannot be changed through the shell either.")
            if is_content_guarded(rel) and CONN_STRING_RE.search(command):
                block(f"this command writes a hardcoded connection string into {target}. "
                      "Connection strings must come from environment variables.")


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        block("hook received malformed JSON; failing closed.")
        return

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    cwd = payload.get("cwd")

    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        guard_file_tool(tool, tool_input, cwd)
    elif tool in ("Bash", "PowerShell"):  # Claude Code on Windows may use either
        guard_bash(tool_input, cwd)
    sys.exit(0)


if __name__ == "__main__":
    main()
