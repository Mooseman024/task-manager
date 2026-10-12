# Task 2: Notification Preference Decomposition

Feature: users get a `notification_pref` of `email`, `sms`, or `none` (default none).
Storage decision: users are dicts in `USERS` in services/users.py (no database), so the
"nullable column" is a `notification_pref` key whose default is `None`. Sending `"none"`
stores `None`.

Each subagent runs in a fresh Claude Code session (`/clear` between them) with the exact
prompt below. Run `pytest -q` after each one before moving on and record the actual
summary line in the Output cell.

## Subagent table

| Subagent # | Input | Task | Output | Constraint | Hand-off |
|---|---|---|---|---|---|
| SA-1: Data + service layer | services/users.py, utils/errors.py, CLAUDE.md | Add a `notification_pref` field (default `None`) to user records plus `list_users`, `get_notification_pref`, and `set_notification_pref` service functions. | services/users.py (modified)<br>**pytest -q:** _fill in_ | Only modify services/users.py. Do not touch routes/api.py, services/tasks.py, tests/, or utils/errors.py. Do not change the signatures of get_user or create_user. | Function signatures: `list_users() -> list[dict]`, `get_notification_pref(user_id: int) -> str \| None`, `set_notification_pref(user_id: int, pref: str) -> dict`; raises NotFoundError("User") / ValidationError("notification_pref", ...); every user dict has `notification_pref` |
| SA-2: API layer | routes/api.py, services/users.py (read only), CLAUDE.md | Add `GET /users`, `GET /users/<id>/notifications`, and `PATCH /users/<id>/notifications` routes that call the SA-1 functions. | routes/api.py (modified)<br>**pytest -q:** _fill in_ | Only modify routes/api.py. Do not touch services/users.py, services/tasks.py, utils/errors.py, or tests/. Do not read or write `USERS` directly in routes/api.py. | Endpoint contract: PATCH body `{"notification_pref": "<value>"}`; both notification routes return `{"user_id": id, "notification_pref": value}`; invalid value returns 422, unknown user 404 |
| SA-3: Tests | services/users.py, routes/api.py, tests/test_tasks.py (style reference), CLAUDE.md | Write tests/test_users.py covering the service functions and all three new routes. | tests/test_users.py (new)<br>**pytest -q:** _fill in_ | Only create tests/test_users.py. Do not edit services/users.py, routes/api.py, utils/errors.py, or tests/test_tasks.py. | Final green `pytest -q` run; end of the pipeline |

## Prompts (issue these exactly)

### SA-1
```
Goal: Add notification preferences to users in @services/users.py.
1. Add a "notification_pref" key with default None to every record in USERS, and make
   create_user set "notification_pref": None on new users.
2. Add a module-level constant VALID_NOTIFICATION_PREFS = ("email", "sms", "none").
3. Add list_users() -> list[dict], get_notification_pref(user_id: int) -> str | None,
   and set_notification_pref(user_id: int, pref: str) -> dict.
   set_notification_pref rejects any value not in VALID_NOTIFICATION_PREFS with
   ValidationError("notification_pref", ...), stores None when pref is "none", and
   returns the updated user. Unknown users raise NotFoundError("User").
Context: Follow the pattern of get_user in @services/users.py exactly, including type
hints and Google-style docstrings. Errors come from @utils/errors.py. Follow @CLAUDE.md.
Constraints: Only modify services/users.py. Do not change the signatures of get_user or
create_user. Do not touch routes/api.py, services/tasks.py, tests/, or utils/errors.py.
Verification: Run pytest -q when done.
```

### SA-2
```
Goal: Add three routes to @routes/api.py:
GET /users (returns list_users()),
GET /users/<int:user_id>/notifications, and
PATCH /users/<int:user_id>/notifications (JSON body {"notification_pref": "<value>"}).
Both notification routes return {"user_id": <id>, "notification_pref": <value>}.
Context: The service functions list_users, get_notification_pref, and
set_notification_pref already exist in @services/users.py. Errors are handled by the
existing handle_app_error in routes/api.py. Follow the style of get_user_route.
Constraints: Only modify routes/api.py. Do not touch services/, utils/, or tests/.
Do not read or write USERS directly; call the service functions only.
Verification: Run pytest -q when done.
```

### SA-3
```
Goal: Create tests/test_users.py with tests for list_users, get_notification_pref,
set_notification_pref, and the routes GET /users, GET /users/<id>/notifications, and
PATCH /users/<id>/notifications. Cover: default is None, setting email and sms,
setting "none" stores None, invalid value raises ValidationError / returns 422,
unknown user raises NotFoundError / returns 404, and GET /users and GET /users/<id>
include notification_pref.
Context: See @services/users.py, @routes/api.py, and @tests/test_tasks.py for style.
Use app.test_client() from @app.py for route tests. USERS is a shared module-level
dict, so restore it after each test with a fixture.
Constraints: Only create tests/test_users.py. Do not modify any other file.
Verification: Run pytest -q when done. All tests must pass.
```

## Divergence

<!-- Fill this in from your actual sessions. Answer all three: -->
<!-- 1. Did Claude follow the constraint field for every subagent? If not, which one and what did it do instead? -->
<!-- 2. Did any subagent's output break the next subagent's assumption? How did you recover? -->
<!-- 3. Would you write the decomposition differently a second time? What would you change? -->
