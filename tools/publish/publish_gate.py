"""Publish gate: refuses to publish when the repo layout is messy or the lint rule tests fail.
Usage: python tools/publish/publish_gate.py [repo]   (exit 1 = blocked). Called by tools/publish/publish.ps1."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_layout_lint  # noqa: E402


def _pytest_missing():
    import importlib.util
    return importlib.util.find_spec("pytest") is None


def check_gate(repo, run_tests=True):
    repo = Path(repo)
    report = []
    msgs = repo_layout_lint.check_layout(repo)
    report.extend(msgs)
    ok = not msgs
    tests = repo / "tools" / "lint" / "tests"
    if run_tests and tests.is_dir() and _pytest_missing():
        ok = False
        report.append("[GATE] pytest is not installed on this machine, so the lint tests cannot run: pip install pytest, then publish again.")
    elif run_tests and tests.is_dir():
        r = subprocess.run([sys.executable, "-m", "pytest", str(tests), "-q", "-p", "no:cacheprovider"], capture_output=True, text=True, cwd=str(repo))
        if r.returncode != 0:
            ok = False
            report.append("[GATE] lint tests failed (python -m pytest tools/lint/tests -q); fix the rule or its fixtures before publishing.\n" + r.stdout[-800:])
    return ok, "\n".join(report)


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent.parent)
    ok, report = check_gate(repo)
    print(report if report else "publish gate: layout clean, lint tests pass")
    sys.exit(0 if ok else 1)
