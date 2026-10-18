# RETRO.md (Week 6)

> Outline only. Replace each block with your own paragraph after the sessions. Every
> paragraph must cite evidence: a COMMAND_LOG row, a vector number, a file path, a command.

## 1. Slash command value
Pick the command that saved the most typing (likely scaffold-endpoint, COMMAND_LOG row 2).
Write out the ad-hoc prompt you would have needed: four file paths, "follow update_task_route
in routes/api.py", the no-logic and no-data["..."] rules from CLAUDE.md, the 201/200/204
status rules, the test fixture pattern. Then say why the file is better: same constraints every
run, in git, and the fix from your iteration is kept instead of lost in chat history.

## 2. Hook reliability
Vector 1 and Vector 2 results (HOOK_LOG.md and the check_vectors.py table). The point: Part A
had Bash in its branch and utils/errors.py in BLOCKED_PATHS, yet Vector 2 wrote the file, and
on Windows Vector 1 overwrote the real file through a capital U. "Registered in settings.json"
only means the script runs; enforcement is only as good as the input shapes it checks.

## 3. Advisory vs. deterministic
Candidate rule still in CLAUDE.md: "Do not access TASKS or USERS from routes/api.py."
Why advisory: PreToolUse sees the text being written, and a regex for `TASKS`/`USERS` in
routes/api.py would false-positive on comments and miss indirect access through a helper.
Graduation condition (must be specific), e.g.: "If any scaffold-endpoint run (COMMAND_LOG row 2
or later) puts a store import or lookup in routes/api.py, I add a content guard on routes/api.py
that blocks `from services.\w+ import .*\b[A-Z]{2,}\b` and `\b(TASKS|USERS)\[`."

## 4. Limits of hooks
A rule PreToolUse could not enforce, with evidence. Options:
- The four "Known remaining gaps" in HOOK_LOG.md ($VAR indirection, script files, cd + relative
  write, symlinks): PreToolUse sees the command string, not what it does at runtime. Right
  mechanism: OS-level read-only permission on utils/errors.py, or a Stop hook / CI step that
  fails if `git diff --name-only` lists a protected path.
- "pytest must pass after every edit" (in audit-errors' Verification): PreToolUse runs before
  the edit exists, so it cannot know. Right mechanism: a PostToolUse hook on Write|Edit running
  `pytest -q`, which feeds failures back to Claude.
