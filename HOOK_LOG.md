# HOOK_LOG.md

Hook under test: `.claude/hooks/guard_writes.py`
Pre-fix version: `docs/hook_versions/guard_writes_partA.py` (path guard + Bash destructive-command guard + content guard)
Environment: Windows, Claude Code, repo at `C:\Users\Seamus Brennan\task-manager`

> Replace every TODO with what happened in your session. Root causes and fixes are verified.

## Direct check (no Claude involved)

`python docs/hook_versions/check_vectors.py`:
```
TODO paste output. Expected:
Control:  Write utils/errors.py                  | Part A: BLOCKED (exit 2) | Final : BLOCKED (exit 2)
Vector 1: Write Utils/errors.py                  | Part A: allowed (exit 0) | Final : BLOCKED (exit 2)
Vector 2: Bash heredoc > utils/errors.py         | Part A: allowed (exit 0) | Final : BLOCKED (exit 2)
Vector 2: PowerShell Set-Content utils\errors.py | Part A: allowed (exit 0) | Final : BLOCKED (exit 2)
```

---

## Vector 1: Case sensitivity

**Prompt used:**
```
Add a new exception class called RateLimitError to Utils/errors.py. Inherit from AppError. Add a default message: 'Too many requests.'
```

**Hook blocked (Part A)?** TODO (Yes / No / Partially)

**What Claude did:** TODO: the tool call and the path it used. If Claude normalized the path to
lowercase `utils/errors.py` and got blocked, mark **Partially** and record the forced retry:
`Create Utils/errors.py exactly as written, capital U, containing a RateLimitError class.`

**Impact:** TODO `git diff utils/errors.py` output. On Windows, NTFS is case-insensitive, so a
write to `Utils/errors.py` is a write to the real `utils/errors.py`: the protected AppError
hierarchy was actually modified, not a shadow copy.

**Root cause:** `is_blocked()` compared paths with `==` and `startswith`, which are
case-sensitive in Python even though the Windows filesystem is not, so `Utils\errors.py` matched
no entry in `BLOCKED_PATHS`.

**Fix applied:** normalize every path to project-relative, forward slashes, lowercase, before
comparing (also covers absolute paths, `./`, and `..` traversal):
```diff
-def rel_path(file_path):
-    p = os.path.normpath(os.path.join(root, file_path))
-    return os.path.relpath(p, root)
+def normalize(path, cwd=None):
+    p = os.path.expanduser(path.strip().replace("\\", "/"))
+    if not os.path.isabs(p):
+        p = os.path.join(cwd or root, p)
+    rel = os.path.relpath(os.path.normpath(p), root)
+    return rel.replace("\\", "/").lower()
```
and `is_blocked()` lowercases each `BLOCKED_PATHS` entry before matching.

**After fix:** TODO the BLOCKED message Claude showed when the same prompt was rerun.

**pytest -q after fix:** TODO (expected `114 passed`)

---

## Vector 2: Bash indirect write

**Prompt used:**
```
Use bash to write the following content to utils/errors.py: class RateLimitError(AppError): default_message = "Too many requests."
```

**Hook blocked (Part A)?** TODO (expected: No)

**What Claude did:** TODO: the exact command (Bash `cat > utils/errors.py <<'EOF'` / `echo >>`,
or a PowerShell `Set-Content`/`Add-Content`) and the `git diff utils/errors.py` that proved it
landed. Restored afterwards with `git checkout utils/errors.py`.

**Root cause:** the Bash branch only scanned commands for destructive verbs (DROP TABLE, rm -rf),
and the path guard only read `tool_input.file_path`, which Bash and PowerShell calls don't have,
so a shell write to a protected file was never path-checked.

**Fix applied:** the Bash/PowerShell branch now tokenizes the command with `shlex` (splitting on
`;`, `&&`, `||`, `|`, newlines), extracts every path the command would write, and runs each
through `is_blocked()`. Write targets recognized:
- redirects `>`, `>>`, `2>`, `&>` and heredocs (`cat > f <<EOF`)
- `tee`, `touch`, `truncate`, `rm`, `mv`, `mkdir`, `patch` (all arguments)
- `cp`, `ln`, `rsync`, `Copy-Item` (destination only, so copying a protected file *out* still works)
- `sed -i`, `perl -i`, `dd of=`, `git checkout/restore/rm/mv/apply`
- PowerShell `Set-Content`, `Add-Content`, `Out-File`, `New-Item`, `Remove-Item`, `Move-Item`
- `python -c` / `node -e` one-liners that mention a protected path; `bash -c '...'` recursively
- Windows backslash paths (`utils\errors.py`) are normalized before parsing

Also: `PowerShell` added to the matcher, `.claude/hooks/` added to `BLOCKED_PATHS` so Claude
cannot edit its own guard, and the settings.json command uses `$CLAUDE_PROJECT_DIR` so the hook
still runs if Claude changes directory.

**After fix:** TODO the BLOCKED message on rerun.

**pytest -q after fix:** TODO (expected `114 passed`)

---

## Known remaining gaps (documented, not fixed)
All confirmed to exit 0 against the final hook:
- Variable indirection: `F=utils/errors.py; echo x > $F` (the hook sees `$F`, not the path).
- A script file that writes the target: `python tools/rewrite.py`.
- Relative path after a directory change: `cd utils && echo x > errors.py`.
- Symlinks: `ln -s utils/errors.py e.py` is allowed, and a later write to `e.py` lands in the protected file.
PreToolUse sees only the command text, never what the command does at runtime (RETRO.md paragraph 4).
