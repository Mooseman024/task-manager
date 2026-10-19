# RETRO.md (Week 6)

## 1. Slash command value

`/scaffold-endpoint` saved the most prompt-writing (COMMAND_LOG rows 2 and 2v2). Without it, every
new endpoint needs an ad-hoc prompt like: "Add POST /api/tags. Put a thin route in routes/api.py
that follows update_task_route, not create_task_route, and don't index data[...] or import the
store. Put the logic in a new services/tags.py with type hints and Google docstrings, add a
schemas/tags.py with a TypedDict and REQUIRED_FIELDS, add tests/test_tags.py using the deepcopy
reset fixture and a test client, assert 201, and run pytest -q." That's about ten constraints I
would have to remember and retype each time, and in row 2 even the full list missed something:
the service copied update_task's `for field in data` loop, so a null JSON body returned a 500.
Because the prompt lives in a file, I fixed it once (the body-must-be-a-dict constraint and the
two 422 tests) and row 2v2 got it right. An ad-hoc prompt would have lost that fix the moment the
session ended.

## 2. Hook reliability

Both bypass vectors got through the Part A hook (HOOK_LOG.md and the check_vectors.py table).
For Vector 1, Claude's first attempt never reached the hook: it refused on its own after reading
the `## Hooks` section of CLAUDE.md. When I told it to let the hook decide, it edited
`Utils/errors.py`, the case-sensitive comparison let it through, and because NTFS is
case-insensitive the edit landed in the real `utils/errors.py`. For Vector 2, Claude ran
`cat >> utils/errors.py << 'EOF'` and the class was appended, because the Bash branch only checked
for destructive verbs and the path guard only read `file_path`. At that point settings.json
matched Bash and BLOCKED_PATHS listed utils/errors.py, so on paper the rule was configured. In
practice it was only enforced for the one input shape I had tested (a lowercase path through
Write/Edit). Registering a hook proves the script runs; it doesn't prove the script checks every
way the action can happen. Claude's own reports weren't reliable either: during the Vector 2 rerun
the collapsed transcript showed only "Read 1 file" next to a claim that the hook blocked it, and I
had to expand the view to confirm the Bash call actually ran.

## 3. Advisory vs. deterministic

"Do not access TASKS or USERS from routes/api.py" is still advisory in CLAUDE.md's Do-not-touch
section. I left it there because a PreToolUse check can only look at the text being written, and
a regex for `TASKS` or `USERS` in routes/api.py would trip on comments and docstrings while missing
indirect access through a helper function. So far it hasn't been violated: in rows 2 and 2v2,
`/scaffold-endpoint` kept create_tag_route to `request.get_json()` plus one service call. I would
graduate it to a content guard on routes/api.py (blocking `from services.<x> import` of an
uppercase store name and any `TASKS[`/`USERS[`/`TAGS[` lookup) the first time any agent session
writes a store import or store lookup into routes/api.py, even if I catch it in review before it
reaches a commit.

## 4. Limits of hooks

I wanted to enforce "a service function that takes a request body must reject non-dict input with
a 422, never a 500," which is the bug from COMMAND_LOG row 2. PreToolUse was the wrong mechanism:
it runs before the edit exists and sees only the proposed text, so it can't tell whether the new
code actually handles a null body. The only honest check is to run the code. HOOK_LOG's remaining
gaps show the same limit from the other side: `F=utils/errors.py; echo x > $F`, a Python script
that writes the file, or `cd utils && echo x > errors.py` all exit 0, because PreToolUse sees the
command string, not what the command does at runtime. The right mechanisms are a PostToolUse hook
on Write|Edit that runs pytest -q (with tests like the 422 cases from row 2v2) and feeds failures
back to Claude, plus OS-level read-only permissions or a CI check on `git diff --name-only` for the
protected files.
