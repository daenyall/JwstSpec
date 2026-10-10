
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"

try:
    event = json.load(sys.stdin)
except (ValueError, OSError):
    event = {}


# Prevent repeated automatic continuation.
if event.get("stop_hook_active"):
    sys.exit(0)

checks = [
    ("Git diff", ["git", "diff", "--check"], ROOT),
    (
        "Git staged diff",
        ["git", "diff", "--cached", "--check"],
        ROOT,
    ),
]

# Only run frontend checks when there are local frontend changes.
status = subprocess.run(
    ["git", "status", "--porcelain", "--", "frontend"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    timeout=10,
)

if status.returncode != 0:
    checks.append(
        ("Git status", ["git", "status", "--porcelain"], ROOT)
    )
elif status.stdout.strip():
    checks.extend([
        ("ESLint", ["npm", "run", "lint"], FRONTEND),
        (
            "TypeScript",
            [
                "./node_modules/.bin/tsc",
                "--noEmit",
                "--incremental",
                "false",
            ],
            FRONTEND,
        ),
    ])

failures = []


# Run backend tests when backend files have changed.
backend_status = subprocess.run(
    ["git", "status", "--porcelain", "--", "backend"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    timeout=10,
)

if backend_status.returncode != 0:
    checks.append((
        "Git backend status",
        ["git", "status", "--porcelain", "--", "backend"],
        ROOT,
    ))

elif backend_status.stdout.strip():
    python = ROOT / "backend" / ".venv" / "bin" / "python"

    if not python.is_file():
        worktrees = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )

        main_root = next(
            (
                Path(line[len("worktree "):])
                for line in worktrees.stdout.splitlines()
                if line.startswith("worktree ")
            ),
            ROOT,
        )

        candidate = main_root / "backend" / ".venv" / "bin" / "python"

        current_requirements = ROOT / "backend" / "requirements.txt"
        main_requirements = main_root / "backend" / "requirements.txt"

        if (
            worktrees.returncode == 0
            and candidate.is_file()
            and current_requirements.is_file()
            and main_requirements.is_file()
            and current_requirements.read_bytes()
            == main_requirements.read_bytes()
        ):
            python = candidate

    checks.append((
        "Backend pytest",
        [str(python), "-m", "pytest", "tests", "-q"],
        ROOT / "backend",
    ))


for name, command, cwd in checks:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=55,
        )
        if result.returncode != 0:
            output = (result.stdout + result.stderr)[-2500:]
            failures.append(f"{name} failed:\n{output}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        failures.append(f"{name} could not complete: {exc}")

if failures:
    reason = (
        "Final validation failed. Investigate the following "
        "results, fix issues caused by your changes, and rerun "
        "relevant checks. Preserve unrelated user changes. "
        "Report any pre-existing or unresolved failures.\n\n"
        + "\n\n".join(failures)
    )[:6500]

    print(json.dumps({
        "decision": "block",
        "reason": reason,
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "decision": "block",
            "reason": reason,
        },
    }))
else:
    print(json.dumps({"decision": "allow"}))
