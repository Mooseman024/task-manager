# Task Manager

Python Flask API for managing tasks and users. Data is held in in-memory dicts (no database).

## Commands
- Install: pip install -r requirements.txt
- Run all tests: pytest -v
- Quick test check after each change: pytest -q
- Run the API locally: python app.py (serves under /api on port 5000)
- After changing services/users.py or routes/api.py user routes: pytest -q tests/test_users.py
  (a full pytest -q stays green if no user tests exist yet, as it did after Task 2 SA-1 and SA-2)

## Architecture
- app.py creates the Flask app and registers the `api` blueprint from routes/api.py at /api.
- routes/api.py: HTTP only. Parse the request, call a service function, return jsonify(...).
- services/tasks.py and services/users.py: business logic and validation. Each owns its
  data store (TASKS and USERS dicts).
- utils/errors.py: AppError base class plus NotFoundError (404) and ValidationError (422).
  handle_app_error in routes/api.py turns any AppError into a JSON error response.
- Canonical example of a service function: get_user in services/users.py.
- Boundary between services/ and routes/: routes/api.py passes raw request values (query strings,
  JSON bodies) straight to a service function; parsing, validation and data access happen in
  services/, following get_user in services/users.py and update_task in services/tasks.py.

## Conventions
- Every function has type hints on all arguments and the return value.
- Every service function has a Google-style docstring with Args, Returns, and Raises,
  matching services/users.py.
- Missing records raise NotFoundError("Task") or NotFoundError("User"), never a raw KeyError.
- Bad input raises ValidationError(field, reason) from utils/errors.py, never a plain Exception.
- New tests go in tests/, one file per service (tests/test_tasks.py, tests/test_users.py).

## Do not touch
- Do not edit utils/errors.py. Use the existing AppError subclasses.
- Do not remove, rename, or reorder parameters of existing functions in services/tasks.py or
  services/users.py. New parameters must be keyword arguments with defaults.
- Do not access TASKS or USERS from routes/api.py. Routes call service functions only.
- Do not remove or weaken existing tests in tests/test_tasks.py to make a change pass.
- When editing routes/api.py, do not index the JSON body (data["..."]); pass the body to a
  function in services/users.py or services/tasks.py that raises ValidationError for missing fields.
- When editing routes/api.py, do not import USERS, TASKS, or ValidationError.
- When writing tests/test_users.py or tests/test_tasks.py, do not edit services/ or routes/api.py
  to make a test pass.
