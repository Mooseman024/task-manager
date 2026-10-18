"""Run both bypass vectors against the Part A and final hooks; print exit codes.

Usage (from the repo root):  python docs/hook_versions/check_vectors.py
Exit 0 = allowed, exit 2 = blocked. Paste the output into HOOK_LOG.md.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = {
    "Part A": ROOT / "docs" / "hook_versions" / "guard_writes_partA.py",
    "Final ": ROOT / ".claude" / "hooks" / "guard_writes.py",
}
CASES = [
    ("Control:  Write utils/errors.py",
     {"tool_name": "Write", "tool_input": {"file_path": "utils/errors.py", "content": "x"}}),
    ("Vector 1: Write Utils/errors.py",
     {"tool_name": "Write", "tool_input": {"file_path": "Utils/errors.py", "content": "x"}}),
    ("Vector 2: Bash heredoc > utils/errors.py",
     {"tool_name": "Bash", "tool_input": {"command": "cat > utils/errors.py <<'EOF'\nx\nEOF"}}),
    ("Vector 2: PowerShell Set-Content utils\\errors.py",
     {"tool_name": "PowerShell", "tool_input": {"command": "Set-Content utils\\errors.py 'x'"}}),
]

env = {**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)}
for label, payload in CASES:
    row = []
    for name, hook in HOOKS.items():
        code = subprocess.run([sys.executable, str(hook)], input=json.dumps(payload),
                              capture_output=True, text=True, env=env).returncode
        row.append(f"{name}: {'BLOCKED' if code == 2 else 'allowed'} (exit {code})")
    print(f"{label:<48} | " + " | ".join(row))
