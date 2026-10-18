---
description: Scaffold a new endpoint (route + service + schema + test) following the task routes
argument-hint: <resource> <HTTP_METHOD>   e.g. tags POST
---
## Goal
Scaffold a `$2 /api/$1` endpoint for the `$1` resource (arguments received: $ARGUMENTS).
Create or update exactly these files:
- Route file, routes/api.py: add one thin route function for `$2 /$1` on the existing
  `api` blueprint.
- Service file, services/$1.py: the service function the route calls, plus the in-memory
  store (an uppercase dict like TASKS) if the file is new. All logic lives here.
- Schema file, schemas/$1.py: the record shape as a TypedDict and a REQUIRED_FIELDS tuple.
  Create the schemas/ package (with an empty __init__.py) if it does not exist. The service
  validates input against it.
- Test file, tests/test_$1.py: a happy-path route test.

## Context
- This repo has no routes/tasks.py; the task routes in routes/api.py are its canonical
  pattern (list_tasks_route, update_task_route). For a body-carrying method, follow
  update_task_route: pass the whole JSON body to one service function.
- services/tasks.py (update_task) and services/users.py (get_user) show the service pattern:
  type hints, Google-style docstrings, NotFoundError / ValidationError from utils/errors.py.
- tests/test_tasks.py shows the test pattern: an autouse fixture that deep-copies the store
  and restores it, and a `client` fixture from `app.test_client()`.
- app.py already registers the `api` blueprint at /api; no change needed there.

## Constraints
- No business logic in the route handler. It may only read the request, call ONE service
  function, and return jsonify(...) with a status code. No if-statements, no dict lookups,
  no indexing the JSON body (data["..."]), and no importing the store or ValidationError
  into routes/api.py.
- Do not change any existing route, service function, or test. Only add.
- Do not touch utils/errors.py or app.py.
- If `$2` is not GET, POST, PUT, PATCH, or DELETE, or `$1` is missing, stop and ask.

## Verification
- tests/test_$1.py must call the route through the test client and assert the happy-path
  status: POST -> 201, GET/PUT/PATCH -> 200, DELETE -> 204.
- Run pytest -q. The new test and all existing tests must pass.
- Report the files created/changed and the final pytest -q line.
