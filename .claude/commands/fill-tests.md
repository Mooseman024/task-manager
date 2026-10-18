# Use this to add pytest cases for untested functions in one service file; do not use it to fix failing tests or to change source code.

## Goal
Find every public function in $ARGUMENTS that has no direct test and write tests for it.
Done means each previously untested function has at least one happy-path test and one
error-path test (asserting the specific AppError subclass it raises, if it raises one), and
pytest -q passes.

## Context
- Tests for services/X.py go in tests/test_X.py (tests/test_tasks.py, tests/test_users.py).
- There is no conftest.py. Each test file defines its own fixtures: an autouse fixture that
  deep-copies the store (TASKS or USERS) and restores it after each test, and a `client`
  fixture from `app.test_client()`. Reuse the ones already in the target test file.
- Errors come from utils/errors.py: NotFoundError (404) and ValidationError (422).
- To find untested functions, list the `def` lines in $ARGUMENTS and grep the matching test
  file for each function name.

## Constraints
- Only edit the matching test file under tests/. Do not modify $ARGUMENTS, routes/api.py,
  utils/errors.py, or any other source file, even if you find a bug. Report it instead.
- Do not edit, delete, or weaken existing tests.
- Do not add a conftest.py or new fixtures unless the existing ones cannot work; if you must,
  explain why in the summary.
- No network calls, no sleeps, no dependence on test order.

## Verification
- Run pytest -q after adding the tests for each function.
- Every new test must pass. If one fails because the source looks wrong, mark it
  @pytest.mark.xfail(reason="...") and report it rather than changing source.
- Finish with: the functions that were untested, the tests added for each, and the final
  pytest -q line.
