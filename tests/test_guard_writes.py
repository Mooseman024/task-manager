"""Tests for .claude/hooks/guard_writes.py.

Each case pipes a PreToolUse payload into the hook and checks the exit code
(0 = allowed, 2 = blocked). Runs as part of the normal pytest -q suite.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "guard_writes.py"


def run_hook(tool, tool_input):
    payload = {"tool_name": tool, "tool_input": tool_input, "cwd": str(ROOT)}
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)}
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                          capture_output=True, text=True, env=env, timeout=10)
    return proc.returncode, proc.stderr


def write(path, content="x = 1\n"):
    return run_hook("Write", {"file_path": path, "content": content})


def bash(cmd):
    return run_hook("Bash", {"command": cmd})


# ── Path guard ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("path", [
    "utils/errors.py",
    str(ROOT / "utils" / "errors.py"),          # absolute path (what Claude sends)
    "./utils/errors.py",
    "services/../utils/errors.py",              # traversal
    "Utils/errors.py",                          # Vector 1: case
    "UTILS/ERRORS.PY",
    "utils\\errors.py",                        # Windows separators
    ".env",
    ".claude/settings.json",
    ".claude/hooks/guard_writes.py",
])
def test_protected_paths_blocked(path):
    assert write(path)[0] == 2


@pytest.mark.parametrize("path", [
    "services/tasks.py",
    "routes/tasks.py",
    "utils/helpers.py",            # sibling of a protected file
    "utils/errors_notes.md",       # lookalike name, not the protected file
    "app.py",
    ".env.example",
])
def test_normal_paths_allowed(path):
    assert write(path)[0] == 0


def test_edit_and_multiedit_on_protected_path():
    assert run_hook("Edit", {"file_path": "utils/errors.py",
                             "old_string": "a", "new_string": "b"})[0] == 2
    assert run_hook("MultiEdit", {"file_path": "utils/errors.py",
                                  "edits": [{"old_string": "a", "new_string": "b"}]})[0] == 2


# ── Bash guard: destructive commands ────────────────────────────────────────
@pytest.mark.parametrize("cmd", [
    "sqlite3 app.db 'DROP TABLE tasks;'",
    "psql -c \"drop   table users\"",
    "psql -c 'TRUNCATE TABLE tasks'",
    "rm -rf build",
    "rm -fr /tmp/x",
    "rm -r -f src",
    "rm --recursive --force src",
    "sudo rm -Rf /",
    "cd x && rm -rf .",
    "git reset --hard HEAD~1",
    "Remove-Item -Recurse -Force build",
    "remove-item build -r -fo",
    "git push --force origin main",
    "git push -f",
])
def test_destructive_bash_blocked(cmd):
    assert bash(cmd)[0] == 2


@pytest.mark.parametrize("cmd", [
    "pytest -q",
    "rm build/old.log",                 # rm without -rf is fine
    "rm -r empty_dir",                  # recursive without force
    "echo dropdown table",              # word boundary: not DROP TABLE
    "grep -rf patterns.txt src",        # -rf on a non-rm command
    "git push origin feature-fix",
    "git reset --soft HEAD~1",
    "Remove-Item build/old.log",
    "cat utils/errors.py",              # reading a protected file is fine
    "cp utils/errors.py /tmp/errors_backup.py",
    "grep -n AppError utils/errors.py",
])
def test_safe_bash_allowed(cmd):
    assert bash(cmd)[0] == 0


# ── Bash guard: indirect writes to protected paths (Vector 2) ───────────────
@pytest.mark.parametrize("cmd", [
    "echo 'class X: pass' > utils/errors.py",
    "echo 'class X: pass' >> utils/errors.py",
    "cat > utils/errors.py <<'EOF'\nclass X: pass\nEOF",
    "printf 'x' | tee utils/errors.py",
    "printf 'x' | tee -a Utils/errors.py",
    "sed -i 's/AppError/Err/' utils/errors.py",
    "cp /tmp/evil.py utils/errors.py",
    "mv utils/errors.py utils/errors_old.py",
    "rm utils/errors.py",
    "touch .claude/hooks/evil.py",
    "python3 -c \"open('utils/errors.py','w').write('x')\"",
    "bash -c 'echo x > utils/errors.py'",
    "git checkout -- utils/errors.py",
    "echo SECRET=1 > .env",
    "dd if=/dev/zero of=utils/errors.py",
])
def test_bash_indirect_writes_blocked(cmd):
    assert bash(cmd)[0] == 2


# ── PowerShell tool (Claude Code on Windows) ────────────────────────────────
@pytest.mark.parametrize("cmd", [
    "Set-Content -Path utils/errors.py -Value 'x'",
    "Set-Content utils\\errors.py 'x'",
    "'x' | Out-File -FilePath Utils\\errors.py",
    "Add-Content utils/errors.py 'class X: pass'",
    "Copy-Item C:/tmp/evil.py -Destination utils/errors.py",
    "Remove-Item utils/errors.py",
    "echo x > utils\\errors.py",
])
def test_powershell_writes_blocked(cmd):
    assert run_hook("PowerShell", {"command": cmd})[0] == 2


def test_powershell_read_allowed():
    assert run_hook("PowerShell", {"command": "Get-Content utils/errors.py"})[0] == 0


# ── Content guard ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("conn", [
    "postgresql://user:pw@localhost/tasks",
    "postgresql+psycopg2://u:p@db/tasks",
    "sqlite:///tasks.db",
])
def test_conn_string_blocked_in_guarded_file(conn):
    src = f'ENGINE_URL = "{conn}"\n'
    assert write("services/tasks.py", src)[0] == 2
    assert run_hook("Edit", {"file_path": "services/tasks.py",
                             "old_string": "a", "new_string": src})[0] == 2
    assert run_hook("MultiEdit", {"file_path": "services/tasks.py",
                                  "edits": [{"old_string": "a", "new_string": "ok"},
                                            {"old_string": "b", "new_string": src}]})[0] == 2
    assert bash(f"echo '{src.strip()}' >> services/tasks.py")[0] == 2


def test_env_var_connection_allowed():
    src = 'import os\nENGINE_URL = os.environ["DATABASE_URL"]\n'
    assert write("services/tasks.py", src)[0] == 0


def test_conn_string_allowed_in_unguarded_file():
    # Only services/tasks.py is content-guarded; config/tests may reference URLs.
    assert write("tests/conftest.py", 'URL = "sqlite:///:memory:"\n')[0] == 0


# ── Robustness ──────────────────────────────────────────────────────────────
def test_block_message_goes_to_stderr():
    code, err = write("utils/errors.py")
    assert code == 2 and "BLOCKED" in err


def test_other_tools_ignored():
    assert run_hook("Read", {"file_path": "utils/errors.py"})[0] == 0
