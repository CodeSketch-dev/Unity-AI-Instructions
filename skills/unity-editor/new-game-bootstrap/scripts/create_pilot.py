"""Copy a bundled Unity template into an empty local pilot destination."""
import argparse
import os
import shutil
import sys

SKIP = {"Library", "Temp", "obj", "Logs", "Build", "Builds", ".git", "UserSettings"}


def copy_template(source, destination, dry_run=False):
    if not os.path.isdir(source):
        return 2, "source template not found"
    if os.path.exists(destination) and os.listdir(destination):
        return 2, "destination is not empty"
    if dry_run:
        return 0, "[dry run] would copy template"
    os.makedirs(destination, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*SKIP))
    return 0, "copied template"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True)
    ap.add_argument("--destination", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    code, message = copy_template(a.source, a.destination, a.dry_run)
    print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
