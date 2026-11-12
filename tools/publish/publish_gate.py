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
    targets = [str(p) for p in [repo / "tools" / "lint" / "tests"] if p.is_dir()]
    targets += [str(p) for p in sorted((repo / "tools" / "tests").glob("test_harness_*.py"))]
    if run_tests and targets and _pytest_missing():
        ok = False
        report.append("[GATE] pytest is not installed on this machine, so the lint and harness tests cannot run: pip install pytest, then publish again.")
    elif run_tests and targets:
        r = subprocess.run([sys.executable, "-m", "pytest", *targets, "-q", "-p", "no:cacheprovider"], capture_output=True, text=True, cwd=str(repo))
        if r.returncode != 0:
            ok = False
            report.append("[GATE] lint tests and harness tests failed (python -m pytest tools/lint/tests tools/tests/test_harness_*.py -q); fix the rule, harness code or fixtures before publishing.\n" + r.stdout[-800:])
    return ok, "\n".join(report)


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent.parent)
    ok, report = check_gate(repo)
    print(report if report else "publish gate: layout clean, lint tests pass")
    sys.exit(0 if ok else 1)
