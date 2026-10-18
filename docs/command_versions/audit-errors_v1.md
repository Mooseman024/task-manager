---
description: Replace raw exceptions in one service file with existing AppError subclasses
argument-hint: <services/file.py>
---
## Goal
Audit $ARGUMENTS for missing AppError handling. For every function that raises a raw
exception (ValueError, TypeError, Exception) or lets one escape (for example a bare
`TASKS[task_id]` lookup that can raise KeyError), raise the matching existing AppError
subclass instead: NotFoundError("<Resource>") for a missing record, ValidationError(field,
reason) for bad input. Done means no function in $ARGUMENTS can raise a raw exception for a
missing record or bad input, and pytest -q passes.

## Context
- Canonical pattern: get_user in services/users.py (checks `if user_id not in USERS:` and
  raises NotFoundError("User") before indexing). Match it exactly.
- AppError hierarchy: utils/errors.py defines AppError, NotFoundError(resource) -> 404 and
  ValidationError(field, reason) -> 422. Read it first.
- CLAUDE.md conventions apply: type hints on every argument and return, and a Google-style
  docstring with Args, Returns, and Raises on every service function you change.

## Constraints
- Scope lock: edit ONLY $ARGUMENTS. Do not touch utils/errors.py, services/users.py,
  routes/api.py, or anything under tests/. If a fix seems to need another file, stop and
  report it instead of making the change.
- Idempotency: if a function already raises the correct AppError subclass (like get_user,
  update_task, or _validate_priority), skip it. Do not reword its message, reformat it, or
  touch its docstring. Running this command twice on the same file must change nothing the
  second time.
- If every function already complies, make no edits and reply "No changes needed" with the
  list of functions you checked.
- Do not add new AppError subclasses. Use only the existing ones.
- Do not remove, rename, or reorder any function's parameters.
- No blanket try/except. Check the condition explicitly, the way get_user does.

## Verification
- Run pytest -q after every function you change, not once at the end. It must pass before
  you move to the next function. If it fails, fix or revert that function first.
- Finish with a table: function | before | after (or "skipped: already compliant"), then the
  final pytest -q line.
