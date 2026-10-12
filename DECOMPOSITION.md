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
| SA-1: Data + service layer | services/users.py, utils/errors.py, CLAUDE.md | Add a `notification_pref` field (default `None`) to user records plus `list_users`, `get_notification_pref`, and `set_notification_pref` service functions. | services/users.py (modified)<br>**pytest -q:** 27 passed in 0.11s. `git diff --stat`: only services/users.py changed (51+, 3-). | Only modify services/users.py. Do not touch routes/api.py, services/tasks.py, tests/, or utils/errors.py. Do not change the signatures of get_user or create_user. | Function signatures: `list_users() -> list[dict]`, `get_notification_pref(user_id: int) -> str \| None`, `set_notification_pref(user_id: int, pref: str) -> dict`; raises NotFoundError("User") / ValidationError("notification_pref", ...); every user dict has `notification_pref` |
| SA-2: API layer | routes/api.py, services/users.py (read only), CLAUDE.md | Add `GET /users`, `GET /users/<id>/notifications`, and `PATCH /users/<id>/notifications` routes that call the SA-1 functions. | routes/api.py (modified)<br>**pytest -q:** 27 passed in 0.11s. `git diff --stat`: only routes/api.py changed (15+, 1-). Note: 27 is the same count as SA-1, because no user tests existed yet. | Only modify routes/api.py. Do not touch services/users.py, services/tasks.py, utils/errors.py, or tests/. Do not read or write `USERS` directly in routes/api.py. | Endpoint contract: PATCH body `{"notification_pref": "<value>"}`; both notification routes return `{"user_id": id, "notification_pref": value}`; invalid value returns 422, unknown user 404 |
| SA-3: Tests | services/users.py, routes/api.py, tests/test_tasks.py (style reference), CLAUDE.md | Write tests/test_users.py covering the service functions and all three new routes. | tests/test_users.py (new)<br>**pytest -q:** 42 passed. `git status`: only new file tests/test_users.py (15 new tests). | Only create tests/test_users.py. Do not edit services/users.py, routes/api.py, utils/errors.py, or tests/test_tasks.py. | Final green `pytest -q` run; end of the pipeline |

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

**1. Did Claude follow the constraint field for every subagent?**
Yes, at the file level. After each subagent I checked `git diff --stat` (and `git status` for SA-3's new file). SA-1 changed only services/users.py (51+, 3-), SA-2 changed only routes/api.py (15+, 1-), and SA-3 created only tests/test_users.py. For SA-2's "do not read or write USERS" rule, I ran `Select-String -Path routes\api.py -Pattern "USERS|ValidationError" -CaseSensitive`, which returned nothing, so routes/api.py calls only `list_users`, `get_notification_pref`, and `set_notification_pref`. My first run of that search was case-insensitive and matched every "users" in the URL strings, which was a false alarm.

**2. Did any subagent's output break the next subagent's assumption? How did you recover?**
Yes. SA-2 broke the hand-off contract I wrote for it ("invalid value returns 422, unknown user 404"). `set_notification_pref_route` in routes/api.py does `set_notification_pref(user_id, data["notification_pref"])`, so a PATCH body without `notification_pref` raises KeyError and returns 500 instead of 422. PATCH /users/999/notifications with `{}` also returns 500, not 404, because the KeyError fires before the service's user lookup. pytest -q stayed at 27 passed after SA-2, because no user tests existed until SA-3. SA-3 also missed it, because its prompt listed "invalid value" but not "missing field", and tests/test_users.py only tests the cases its prompt named. I did not recover inside the pipeline: the spec requires issuing the exact DECOMPOSITION.md prompts, and the suite was green, so there was no red state to fix in-session. It is documented here as a known defect, and the fix belongs in a follow-up subagent.

**3. Would you write the decomposition differently a second time?**
Yes, in two ways. First, I would put the request body handling on the service side of the boundary: `set_notification_pref(user_id, data: dict)`, following `update_task(task_id, data)` in services/tasks.py from Task 1 Session 2, so routes/api.py never indexes the JSON body. In Task 1 I caught the identical `data["priority"]` KeyError in the Session 2 plan review, but SA-2 had no plan review, and it shipped the same bug. Second, I would derive SA-3's test list from SA-2's Hand-off column (every status code in the contract, including missing field → 422), so the test subagent checks the contract instead of only the cases I happened to list in its prompt.
